from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin
from .forms import *


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'nome', 'user_type', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'groups')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('nome', 'nascimento', 'telefone', 'email', 'estado', 'cidade', 'publico', 'bio', 'preco', 'sexo', 'idioma')}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'nome', 'nascimento', 'telefone', 'user_type', 'password1', 'password2'),
        }),
    )

admin.site.register(Evento)
admin.site.register(CustomUser, CustomUserAdmin)