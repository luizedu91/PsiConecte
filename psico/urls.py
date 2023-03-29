from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth.views import PasswordChangeDoneView
from app.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name="home"),
    path('register/', register, name="register"),
    path('logout/', logout_view, name="logout"),
    path('get_cities/<int:region_id>/', get_cities, name='get_cities'),
    path('login/', login_view, name='login'),
    path('home/', home, name='home'),
    path('buscar/', buscar, name='buscar'),
    path('agendamento/', agendamento, name='agendamento'),
    path('agendamento/<uuid:uuid>/', agendamento, name='agendamento'),
    path('confirmado/<uuid:confirmation_token>/', confirmado, name='confirmado'),
    path('perfil/<uuid:user_uuid>/', perfil, name='perfil'),
    path('atualizar_notas/<int:agendamento_id>/', atualizar_notas, name='atualizar_notas'),
    path('cancelar_agendamento/<int:agendamento_id>/', cancelar_evento, name='cancelar_evento'),
    path('editar_perfil/', editar_perfil, name='editar_perfil'),
    path('mudar_senha/', custom_password_change, name='mudar_senha')
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

