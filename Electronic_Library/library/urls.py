from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('books/', views.book_list, name='book_list'),
    path('books/<int:pk>/', views.book_detail, name='book_detail'),
    
    # User actions
    path('books/<int:book_id>/borrow/', views.borrow_book, name='borrow_book'),
    path('my-loans/', views.my_loans, name='my_loans'),
    path('export/', views.export_data, name='export_data'),
    path('profile/', views.profile, name='profile'),
    
    # Authentication
    path('accounts/login/', views.user_login, name='login'),
    path('accounts/logout/', views.user_logout, name='logout'),
    path('accounts/register/', views.register, name='register'),
    
    # Admin
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/backup-logs/', views.backup_logs, name='backup_logs'),
]