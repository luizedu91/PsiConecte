from django.db import models
from django.contrib.auth.models import AbstractUser, Permission, Group
import uuid
from cities_light.receivers import connect_default_signals
from cities_light.abstract_models import (AbstractCountry, AbstractRegion, AbstractCity, AbstractSubRegion) 

#Classes for multiple choice fields. Populated from the second migration file.
class PublicoAlvo(models.Model):
    publico = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.publico  
class Linguas(models.Model):
    linguas = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.linguas

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('terapeuta', 'Terapeuta'),
        ('paciente', 'Paciente'),
    ]
    GENDER = [
        ('Masculino', 'Masculino'),
        ('Feminino', 'Feminino'),
        ('Outro/Prefiro não indicar', 'Outro/Prefiro não indicar'),
    ]
    SPECIALIZATION_CHOICES = [
        ('TCC', 'Terapia Cognitivo-Comportamental (TCC)'),
        ('Junguiana', 'Psicologia Analítica (Junguiana)'),
        ('Freudiana', 'Psicanálise Freudiana'),
        ('Lacaniana', 'Psicanálise Lacaniana'),
        ('Humanista', 'Psicologia Humanista'),
        ('Positiva', 'Psicologia Positiva'),
        ('Casal_Familia', 'Terapia de Casal e Família'),
        ('Sistemica', 'Terapia Sistêmica'),
        ('Gestalt', 'Terapia Gestalt'),
        ('Esquema', 'Terapia do Esquema'),
        ('Comportamento', 'Análise do comportamento'),
        ('Outra', 'Outra')
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    groups = models.ManyToManyField(Group, related_name='%(app_label)s_%(class)s_groups', blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name='%(app_label)s_%(class)s_permissions', blank=True)
    nome = models.CharField(max_length=100)
    foto = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, default='https://tse2.mm.bing.net/th?id=OIP.Jw-MfZVo8aCZLEVTHvMZbQHaE8&pid=Api')
    nascimento = models.DateField(blank=True, null=True)
    telefone = models.CharField(max_length=30, blank=True, null=True)
    uuid =  models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=50, blank=True, null=True)
    mandar_email = models.BooleanField(blank=True, null = True)
    mandar_whats = models.BooleanField(blank=True, null = True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    cidade = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    preco = models.PositiveIntegerField(default=0, verbose_name='Preço', blank=True, null=True) 
    sexo = models.CharField(max_length=100, choices=GENDER)
    idioma = models.ManyToManyField(Linguas)

    # Terapeuta-specific fields
    especialidade = models.CharField(max_length=100, choices=SPECIALIZATION_CHOICES, blank=True, null=True)
    publico = models.ManyToManyField(PublicoAlvo, blank=True)
    formacao = models.CharField(max_length=100, blank=True, null=True)
    limite_eventos = models.PositiveIntegerField(null=True, blank=True, default=10)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) 
        if self.pk:
            permission = Permission.objects.get(codename='delete_event', content_type__model=Evento._meta.model_name)
            self.user_permissions.add(permission)

#Necessary to make cities_light work.
class Country(AbstractCountry):
    pass
connect_default_signals(Country)   
class Region(AbstractRegion):
    pass
connect_default_signals(Region)
class SubRegion(AbstractSubRegion):
    pass
connect_default_signals(SubRegion)
class City(AbstractCity):
    timezone = models.CharField(max_length=40)
connect_default_signals(City)

class Evento(models.Model):
    terapeuta = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'user_type': 'terapeuta'})
    paciente = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True, limit_choices_to={'user_type': 'paciente'}, related_name='paciente_eventos')
    horario = models.DateTimeField(blank=True, null=True)
    duracao = models.DecimalField(default=0, max_digits=3, decimal_places=0, verbose_name='Duração (min)')
    notas = models.TextField()
    confirmation_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    num_occurrences = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        permissions = [
            ("delete_event", ("Pode deletar agendamentos")),
        ]

#When an appointment is requested and a confirmation email is sent, its data is saved here. After confirmation it is deleted and saved into Evento.
class PendingAgendamento(models.Model):
    confirmation_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    terapeuta = models.ForeignKey(CustomUser, related_name='pending_terapeuta', on_delete=models.CASCADE)
    paciente = models.ForeignKey(CustomUser, related_name='pending_paciente', on_delete=models.CASCADE)
    horario = models.DateTimeField(blank=True, null=True)
    duracao = models.DecimalField(default=0, max_digits=3, decimal_places=0, verbose_name='Duração (min)')
    notas = models.TextField(blank=True, null=True)
    num_occurrences = models.PositiveIntegerField(null=True, blank=True)
