from django.core.management.base import BaseCommand
from app.models import *
import random
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Populates the database with sample appointments.'

    def handle(self, *args, **options):
        num_appointments = 200

        terapeutas = CustomUser.objects.filter(user_type='terapeuta')
        pacientes =  CustomUser.objects.filter(user_type='paciente')

        for i in range(num_appointments):
            evento = Evento.objects.create(
            terapeuta=random.choice(terapeutas),
            paciente=random.choice(pacientes),
            horario=timezone.now() + timedelta(days=random.randint(1, 30), hours=random.randint(0, 23), minutes=random.randint(0, 59)),
            duracao=random.choice([30, 45, 60, 90]),
            notas='Sample appointment notes',
            )   
            
            evento.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated the database with appointments.'))
