from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('librarian', 'Библиотекарь'),
        ('reader', 'Читатель'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='reader'
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)
    registration_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

class Author(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    biography = models.TextField(blank=True, verbose_name='Биография')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    death_date = models.DateField(null=True, blank=True, verbose_name='Дата смерти')
    country = models.CharField(max_length=100, blank=True, verbose_name='Страна')
    photo = models.ImageField(upload_to='authors/', null=True, blank=True)
    
    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"

class Publisher(models.Model):
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
    name = models.CharField(max_length=100, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Родительская категория'
    )
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name

class Book(models.Model):
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'Английский'),
        ('de', 'Немецкий'),
        ('fr', 'Французский'),
        ('es', 'Испанский'),
    ]
    
    title = models.CharField(max_length=500, verbose_name='Название')
    authors = models.ManyToManyField(Author, verbose_name='Авторы')
    isbn = models.CharField(
        max_length=13,
        unique=True,
        verbose_name='ISBN',
        help_text='13 символов'
    )
    publication_year = models.IntegerField(
        verbose_name='Год издания',
        validators=[
            MinValueValidator(1000),
            MaxValueValidator(timezone.now().year)
        ]
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Издательство'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория'
    )
    page_count = models.IntegerField(null=True, blank=True, verbose_name='Количество страниц')
    description = models.TextField(blank=True, verbose_name='Описание')
    cover_image = models.ImageField(
        upload_to='book_covers/',
        null=True,
        blank=True,
        verbose_name='Обложка'
    )
    language = models.CharField(
        max_length=2,
        choices=LANGUAGE_CHOICES,
        default='ru',
        verbose_name='Язык'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['title']
    
    def __str__(self):
        return self.title
    
    @property
    def available_copies(self):
        return self.copies.filter(status='available').count()

class BookCopy(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступна'),
        ('borrowed', 'Выдана'),
        ('reserved', 'Забронирована'),
        ('maintenance', 'В ремонте'),
        ('lost', 'Утеряна'),
    ]
    
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='copies',
        verbose_name='Книга'
    )
    inventory_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Инвентарный номер'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        verbose_name='Статус'
    )
    acquisition_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата поступления'
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Местоположение'
    )
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    class Meta:
        verbose_name = 'Экземпляр книги'
        verbose_name_plural = 'Экземпляры книг'
    
    def __str__(self):
        return f"{self.book.title} ({self.inventory_number})"

class Loan(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('returned', 'Возвращена'),
        ('overdue', 'Просрочена'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loans',
        verbose_name='Пользователь'
    )
    book_copy = models.ForeignKey(
        BookCopy,
        on_delete=models.CASCADE,
        related_name='loans',
        verbose_name='Экземпляр книги'
    )
    loan_date = models.DateField(auto_now_add=True, verbose_name='Дата выдачи')
    due_date = models.DateField(verbose_name='Дата возврата')
    return_date = models.DateField(null=True, blank=True, verbose_name='Фактическая дата возврата')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус'
    )
    
    class Meta:
        verbose_name = 'Выдача книги'
        verbose_name_plural = 'Выдачи книг'
    
    def __str__(self):
        return f"{self.user} - {self.book_copy.book.title}"
    
    def save(self, *args, **kwargs):
        # Автоматическое обновление статуса при возврате
        if self.return_date and self.status != 'returned':
            self.status = 'returned'
            self.book_copy.status = 'available'
            self.book_copy.save()
        super().save(*args, **kwargs)

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('fulfilled', 'Выполнена'),
        ('cancelled', 'Отменена'),
        ('expired', 'Истекла'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='Пользователь'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='Книга'
    )
    reservation_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата бронирования')
    expiration_date = models.DateTimeField(verbose_name='Дата истечения')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус'
    )
    
    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
    
    def __str__(self):
        return f"{self.user} - {self.book.title}"

class Review(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Пользователь'
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Книга'
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Рейтинг'
    )
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ['user', 'book']
    
    def __str__(self):
        return f"{self.user} - {self.book.title} ({self.rating}/5)"

class Fine(models.Model):
    STATUS_CHOICES = [
        ('unpaid', 'Не оплачен'),
        ('paid', 'Оплачен'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='fines',
        verbose_name='Пользователь'
    )
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='fines',
        verbose_name='Выдача'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма штрафа'
    )
    reason = models.TextField(verbose_name='Причина')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='unpaid',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата начисления')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата оплаты')
    
    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафы'
    
    def __str__(self):
        return f"{self.user} - {self.amount} руб."

class BackupLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Успешно'),
        ('error', 'Ошибка'),
    ]
    
    backup_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата резервного копирования')
    file_path = models.CharField(max_length=500, verbose_name='Путь к файлу')
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name='Размер файла')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Статус'
    )
    error_message = models.TextField(blank=True, verbose_name='Сообщение об ошибке')
    execution_time = models.IntegerField(null=True, blank=True, verbose_name='Время выполнения (сек)')
    
    class Meta:
        verbose_name = 'Лог резервного копирования'
        verbose_name_plural = 'Логи резервного копирования'
        ordering = ['-backup_date']
    
    def __str__(self):
        return f"Backup {self.backup_date.strftime('%Y-%m-%d %H:%M:%S')}"
