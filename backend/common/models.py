from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

# Modelo de usuário
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        """
        Cria e retorna um usuário com email e senha.
        """
        if not email:
            raise ValueError("O usuário deve ter um endereço de email.")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        """
        Cria e retorna um superusuário com email e senha.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    birth_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    is_active = models.CharField(default=True)
    
    # Campos padrão de usuários
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'  # O campo usado para autenticação
    REQUIRED_FIELDS = ['name']  # Campos obrigatórios ao criar um superusuário

    def __str__(self):
        return self.name
    
    # Excluir usuário logicamente (mudando is_active para False)
    def delete(self, *args, **kwargs):
        self.is_active = False
        self.save()

# Modelo de endereço
class Address(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=50)
    city = models.CharField(max_length=255)
    zip = models.CharField(max_length=10)

    def __str__(self):
        return f'{self.street}, {self.city}'

# Modelo de livro
class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=255)
    classification = models.CharField(max_length=50)
    status = models.CharField(max_length=50)

    def __str__(self):
        return self.title
