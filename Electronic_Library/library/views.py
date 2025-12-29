from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Q
from django.core.paginator import Paginator
from .models import *
from .forms import *
from .utils import DataExporter

def home(request):
    """Home page view."""
    context = {
        'total_books': Book.objects.count(),
        'total_users': User.objects.count(),
        'active_loans': Loan.objects.filter(status=Loan.Status.ACTIVE).count(),
        'new_books': Book.objects.order_by('-created_at')[:5],
        'popular_books': Book.objects.annotate(
            loan_count=Count('copies__loans')
        ).order_by('-loan_count')[:5],
    }
    return render(request, 'library/home.html', context)

def book_list(request):
    """Book list view with filtering."""
    books = Book.objects.all()
    
    # Filtering
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    author = request.GET.get('author', '')
    
    if search:
        books = books.filter(
            Q(title__icontains=search) |
            Q(isbn__icontains=search) |
            Q(authors__first_name__icontains=search) |
            Q(authors__last_name__icontains=search)
        ).distinct()
    
    if category:
        books = books.filter(category__name__icontains=category)
    
    if author:
        books = books.filter(authors__last_name__icontains=author)
    
    # Pagination
    paginator = Paginator(books, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'search': search,
    }
    return render(request, 'library/book_list.html', context)

def book_detail(request, pk):
    """Book detail view."""
    book = get_object_or_404(Book, pk=pk)
    reviews = book.reviews.all()
    
    context = {
        'book': book,
        'reviews': reviews,
        'available_copies': book.available_copies,
    }
    return render(request, 'library/book_detail.html', context)

@login_required
def borrow_book(request, book_id):
    """Borrow a book."""
    book = get_object_or_404(Book, id=book_id)
    
    if not book.available_copies > 0:
        messages.error(request, 'Нет доступных экземпляров этой книги')
        return redirect('book_detail', pk=book.id)
    
    if request.method == 'POST':
        # Find available copy
        book_copy = book.copies.filter(status=BookCopy.Status.AVAILABLE).first()
        
        # Create loan
        loan = Loan.objects.create(
            user=request.user,
            book_copy=book_copy,
            due_date=timezone.now().date() + timedelta(days=14)
        )
        book_copy.status = BookCopy.Status.BORROWED
        book_copy.save()
        
        messages.success(request, f'Книга "{book.title}" успешно выдана')
        return redirect('my_loans')
    
    return render(request, 'library/borrow_book.html', {'book': book})

@login_required
def my_loans(request):
    """View user's loans."""
    loans = request.user.loans.all()
    context = {
        'loans': loans,
    }
    return render(request, 'library/my_loans.html', context)

@login_required
def export_data(request):
    """Export data view."""
    if request.method == 'GET':
        export_type = request.GET.get('type', 'json')
        model_type = request.GET.get('model', 'books')
        
        if model_type == 'books':
            queryset = Book.objects.all()
            fields = ['title', 'isbn', 'publication_year', 'page_count']
            field_names = ['Название', 'ISBN', 'Год издания', 'Количество страниц']
            columns = ['Название', 'ISBN', 'Год издания', 'Количество страниц', 'Доступные экземпляры']
            title = 'Отчет по книгам'
        elif model_type == 'users':
            queryset = User.objects.all()
            fields = ['username', 'email', 'role', 'date_joined']
            field_names = ['Имя пользователя', 'Email', 'Роль', 'Дата регистрации']
            columns = ['Имя пользователя', 'Email', 'Роль', 'Дата регистрации', 'Активен']
            title = 'Отчет по пользователям'
        elif model_type == 'loans':
            queryset = Loan.objects.filter(status='active')
            fields = ['user__username', 'book_copy__book__title', 'loan_date', 'due_date']
            field_names = ['Пользователь', 'Книга', 'Дата выдачи', 'Срок возврата']
            columns = ['Пользователь', 'Книга', 'Дата выдачи', 'Срок возврата', 'Статус']
            title = 'Отчет по выдачам книг'
        else:
            return HttpResponse("Неправильный тип модели")
        
        if export_type == 'json':
            return DataExporter.export_to_json(queryset, fields)
        elif export_type == 'csv':
            return DataExporter.export_to_csv(queryset, fields, field_names)
        elif export_type == 'pdf':
            return DataExporter.export_to_pdf(queryset, title, columns)
        elif export_type == 'docx':
            return DataExporter.export_to_docx(queryset, title, columns)
        elif export_type == 'xlsx':
            return DataExporter.export_to_xlsx(queryset, title, columns)
        else:
            return HttpResponse("Неправильный формат экспорта")
    
    context = {
        'export_types': ['json', 'csv', 'pdf', 'docx', 'xlsx'],
        'model_types': ['books', 'users', 'loans'],
    }
    return render(request, 'library/export.html', context)

def user_login(request):
    """User login view."""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    
    return render(request, 'registration/login.html')

def user_logout(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('home')

def register(request):
    """User registration view."""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.role = 'reader'
            user.save()
            
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
        'user_loans': request.user.loans.all()[:5],
    }
    return render(request, 'library/profile.html', context)

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'librarian'])
def admin_dashboard(request):
    """Admin dashboard view."""
    stats = {
        'total_books': Book.objects.count(),
        'total_users': User.objects.count(),
        'total_loans': Loan.objects.count(),
        'active_loans': Loan.objects.filter(status=Loan.Status.ACTIVE).count(),
        'overdue_loans': Loan.objects.filter(status=Loan.Status.OVERDUE).count(),
    }
    
    context = {
        'stats': stats,
        'recent_loans': Loan.objects.order_by('-loan_date')[:10],
        'recent_users': User.objects.order_by('-date_joined')[:5],
    }
    return render(request, 'library/admin/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.role in ['admin', 'librarian'])
def backup_logs(request):
    """Backup logs view."""
    logs = BackupLog.objects.all()
    
    context = {
        'logs': logs,
    }
    return render(request, 'library/admin/backup_logs.html', context)