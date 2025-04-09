from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import PickupPoint, User, Book, BookRequest, Address

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'is_active', 'is_staff', 'birth_date', 'phone')
    search_fields = ('name', 'email')
    list_filter = ('is_active', 'is_staff')
    ordering = ('name',)

admin.site.register(User, UserAdmin)
admin.site.register(Book)
admin.site.register(BookRequest)
admin.site.register(Address)
admin.site.register(PickupPoint)