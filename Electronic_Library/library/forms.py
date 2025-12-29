from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import *

class UserRegistrationForm(UserCreationForm):
    """User registration form."""
    
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('ѕользователь с таким email уже существует.')
        return email

class UserProfileForm(forms.ModelForm):
    """User profile form."""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'birth_date']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_id = self.instance.id
        
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            raise ValidationError('ѕользователь с таким email уже существует.')
        return email

class BookForm(forms.ModelForm):
    """Book form."""
    
    class Meta:
        model = Book
        fields = ['title', 'authors', 'isbn', 'publication_year', 'publisher', 
                 'category', 'page_count', 'description', 'cover_image', 'language']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    
    def clean_isbn(self):
        isbn = self.cleaned_data.get('isbn')
        
        if len(isbn) not in [10, 13]:
            raise ValidationError('ISBN должен содержать 10 или 13 символов.')
        
        return isbn

class LoanForm(forms.ModelForm):
    """Loan form."""
    
    class Meta:
        model = Loan
        fields = ['user', 'book_copy', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }