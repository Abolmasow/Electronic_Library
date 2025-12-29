from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import uuid

class User(AbstractUser):
    """Custom user model with role-based permissions."""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        LIBRARIAN = 'librarian', 'Библиотекарь'
        READER = 'reader', 'Читатель'
    
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
        verbose_name='Роль'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    address = models.TextField(blank=True, verbose_name='Адрес')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    registration_date = models.DateField(auto_now_add=True, verbose_name='Дата регистрации')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_librarian(self):
        return self.role == self.Role.LIBRARIAN
    
    @property
    def is_reader(self):
        return self.role == self.Role.READER

class Author(models.Model):
    """Author model."""
    
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    biography = models.TextField(blank=True, verbose_name='Биография')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    death_date = models.DateField(null=True, blank=True, verbose_name='Дата смерти')
    country = models.CharField(max_length=100, blank=True, verbose_name='Страна')
    photo = models.ImageField(upload_to='authors/', null=True, blank=True, verbose_name='Фотография')
    
    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class Publisher(models.Model):
    """Publisher model."""
    
    name = models.CharField(max_length=200, unique=True, verbose_name='Название')
    address = models.TextField(blank=True, verbose_name='Адрес')
    contact_email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    website = models.URLField(blank=True, verbose_name='Веб-сайт')
    
    class Meta:
        verbose_name = 'Издательство'
        verbose_name_plural = 'Издательства'
    
    def __str__(self):
        return self.name

class Category(models.Model):
    """Category model for books."""
    
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='children', verbose_name='Родительская категория')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name

class Book(models.Model):
    """Book model - main entity."""
    
    class Language(models.TextChoices):
        RUSSIAN = 'ru', 'Русский'
        ENGLISH = 'en', 'Английский'
        GERMAN = 'de', 'Немецкий'
        FRENCH = 'fr', 'Французский'
        SPANISH = 'es', 'Испанский'
    
    title = models.CharField(max_length=500, verbose_name='Название')
    authors = models.ManyToManyField(Author, verbose_name='Авторы')
    isbn = models.CharField(max_length=13, unique=True, verbose_name='ISBN')
    publication_year = models.IntegerField(
        verbose_name='Год издания',
        validators=[MinValueValidator(1000), MaxValueValidator(timezone.now().year + 1)]
    )
    publisher = models.ForeignKey(Publisher, on_delete=models.SET_NULL, null=True, verbose_name='Издательство')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name='Категория')
    page_count = models.IntegerField(null=True, blank=True, verbose_name='Количество страниц')
    description = models.TextField(blank=True, verbose_name='Описание')
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True, verbose_name='Обложка')
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.RUSSIAN, verbose_name='Язык')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    @property
    def available_copies(self):
        """Return number of available copies."""
        return self.copies.filter(status=BookCopy.Status.AVAILABLE).count()

class BookCopy(models.Model):
    """Physical copy of a book."""
    
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Доступна'
        BORROWED = 'borrowed', 'Выдана'
        RESERVED = 'reserved', 'Забронирована'
        MAINTENANCE = 'maintenance', 'В ремонте'
        LOST = 'lost', 'Утеряна'
    
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies', verbose_name='Книга')
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name='Инвентарный номер')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE, verbose_name='Статус')
    acquisition_date = models.DateField(null=True, blank=True, verbose_name='Дата поступления')
    location = models.CharField(max_length=100, blank=True, verbose_name='Местоположение')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    class Meta:
        verbose_name = 'Экземпляр книги'
        verbose_name_plural = 'Экземпляры книг'
    
    def __str__(self):
        return f"{self.book.title} ({self.inventory_number})"

class Loan(models.Model):
    """Book loan record."""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Активна'
        RETURNED = 'returned', 'Возвращена'
        OVERDUE = 'overdue', 'Просрочена'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans', verbose_name='Пользователь')
    book_copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='loans', verbose_name='Экземпляр книги')
    loan_date = models.DateField(auto_now_add=True, verbose_name='Дата выдачи')
    due_date = models.DateField(verbose_name='Дата возврата')
    return_date = models.DateField(null=True, blank=True, verbose_name='Фактическая дата возврата')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='Статус')
    
    class Meta:
        verbose_name = 'Выдача книги'
        verbose_name_plural = 'Выдачи книг'
        ordering = ['-loan_date']
    
    def __str__(self):
        return f"{self.user} - {self.book_copy.book.title}"
    
    def save(self, *args, **kwargs):
        # Update status when book is returned
        if self.return_date and self.status != self.Status.RETURNED:
            self.status = self.Status.RETURNED
            self.book_copy.status = BookCopy.Status.AVAILABLE
            self.book_copy.save()
        
        # Check for overdue
        if self.status == self.Status.ACTIVE and self.due_date < timezone.now().date():
            self.status = self.Status.OVERDUE
        
        super().save(*args, **kwargs)

class Reservation(models.Model):
    """Book reservation."""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидание'
        ACTIVE = 'active', 'Активна'
        FULFILLED = 'fulfilled', 'Выполнена'
        CANCELLED = 'cancelled', 'Отменена'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations', verbose_name='Пользователь')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations', verbose_name='Книга')
    reservation_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата бронирования')
    expiration_date = models.DateTimeField(verbose_name='Дата истечения')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='Статус')
    
    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-reservation_date']
    
    def __str__(self):
        return f"{self.user} - {self.book.title}"
    
    def save(self, *args, **kwargs):
        # Set expiration date (7 days from creation)
        if not self.expiration_date:
            self.expiration_date = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

class Review(models.Model):
    """Book review."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', verbose_name='Пользователь')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reviews', verbose_name='Книга')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='Рейтинг')
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.book.title} ({self.rating}/5)"

class Fine(models.Model):
    """Fine for overdue books."""
    
    class Status(models.TextChoices):
        UNPAID = 'unpaid', 'Не оплачен'
        PAID = 'paid', 'Оплачен'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fines', verbose_name='Пользователь')
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='fines', verbose_name='Выдача')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма штрафа')
    reason = models.TextField(verbose_name='Причина')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNPAID, verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата начисления')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата оплаты')
    
    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user} - {self.amount} руб."

class BackupLog(models.Model):
    """Backup operation log."""
    
    class Status(models.TextChoices):
        SUCCESS = 'success', 'Успешно'
        ERROR = 'error', 'Ошибка'
        IN_PROGRESS = 'in_progress', 'В процессе'
    
    backup_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата резервного копирования')
    file_path = models.CharField(max_length=500, verbose_name='Путь к файлу')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='Размер файла (байт)')
    status = models.CharField(max_length=20, choices=Status.choices, verbose_name='Статус')
    error_message = models.TextField(blank=True, verbose_name='Сообщение об ошибке')
    execution_time = models.IntegerField(null=True, blank=True, verbose_name='Время выполнения (сек)')
    
    class Meta:
        verbose_name = 'Лог резервного копирования'
        verbose_name_plural = 'Логи резервного копирования'
        ordering = ['-backup_date']
    
    def __str__(self):
        return f"Backup {self.backup_date.strftime('%Y-%m-%d %H:%M:%S')}"