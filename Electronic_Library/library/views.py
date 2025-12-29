from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .utils.exporters import DataExporter
from .models import Book, Loan, User

class ExportDataView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role in ['admin', 'librarian']
    
    def get(self, request, *args, **kwargs):
        export_type = request.GET.get('type', 'json')
        model_type = request.GET.get('model', 'books')
        
        if model_type == 'books':
            queryset = Book.objects.all()
            fields = ['title', 'isbn', 'publication_year', 'page_count']
            field_names = ['Название', 'ISBN', 'Год издания', 'Количество страниц']
            columns = ['Название', 'ISBN', 'Год издания', 'Количество страниц', 'Доступные экземпляры']
        elif model_type == 'loans':
            queryset = Loan.objects.filter(status='active')
            fields = ['user__username', 'book_copy__book__title', 'loan_date', 'due_date']
            field_names = ['Пользователь', 'Книга', 'Дата выдачи', 'Срок возврата']
            columns = ['Пользователь', 'Книга', 'Дата выдачи', 'Срок возврата', 'Статус']
        elif model_type == 'users':
            queryset = User.objects.all()
            fields = ['username', 'email', 'role', 'date_joined']
            field_names = ['Имя пользователя', 'Email', 'Роль', 'Дата регистрации']
            columns = ['Имя пользователя', 'Email', 'Роль', 'Дата регистрации', 'Активен']
        else:
            return HttpResponseBadRequest("Неправильный тип модели")
        
        if export_type == 'json':
            return DataExporter.export_to_json(queryset, fields)
        elif export_type == 'csv':
            return DataExporter.export_to_csv(queryset, fields, field_names)
        elif export_type == 'pdf':
            return DataExporter.export_to_pdf(queryset, f"Отчет по {model_type}", columns)
        elif export_type == 'docx':
            return DataExporter.export_to_docx(queryset, f"Отчет по {model_type}", columns)
        elif export_type == 'xlsx':
            return DataExporter.export_to_xlsx(queryset, f"Отчет по {model_type}", columns)
        else:
            return HttpResponseBadRequest("Неправильный формат экспорта")
