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
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name
    
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

class PickupPoint(models.Model):
    name = models.CharField(max_length=100)
    street = models.CharField(max_length=255)
    number = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=2)
    zip = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name} - {self.street}, {self.number} - {self.city}/{self.state}"

# Modelo de livro
class Book(models.Model):
    STATUS_CHOICES = (
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
    )

    AGE_CHOICES = (
        ('all_ages', 'Todas as idades'),
        ('10_and_up', '10 anos ou mais'),
        ('13_and_up', '13 anos ou mais'),
        ('16_and_up', '16 anos ou mais'),
        ('18_and_up', '18 anos ou mais'),
    )

    CATEGORY_CHOICES = (
        ('fantasy', 'Fantasia'),
        ('non_fiction', 'Não-ficção'),
        ('adventure', 'Aventura'),
        ('romance', 'Romance'),
        ('horror', 'Horror'),
        ('science_fiction', 'Ficção científica'),
    )

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    classification = models.CharField(max_length=20, choices=AGE_CHOICES)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
    )
    user = models.ForeignKey(User, related_name='books', on_delete=models.CASCADE)
    book_request = models.OneToOneField('BookRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='book_requested')
    pickup_point = models.ForeignKey('PickupPoint', on_delete=models.PROTECT)

    def __str__(self):
        return self.title

# Modelo de solicitação de livro
class BookRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pendente'), 
        ('awaiting_pickup', 'Aguardando Retirada'), 
        ('delivered', 'Entregue'),  
        ('cancelled', 'Cancelada'),
    )

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='book_request_rel')
    user = models.ForeignKey(User, related_name='book_requests', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )

    def __str__(self):
        return f"Request for {self.book.title} by {self.user.name}"
    