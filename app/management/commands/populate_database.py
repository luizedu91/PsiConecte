from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app.models import *
import random
import names
import time


class Command(BaseCommand):
    help = 'Populates the database with sample therapists and patients.'

    def handle(self, *args, **options):
        num_users = 50
        cities = list(City.objects.all())
        regions = list(Region.objects.all())
        linguas = list(Linguas.objects.all())

        for i in range(num_users):
            city = random.choice(cities)
            region = random.choice(regions)
            random_especialidade = random.choice(CustomUser.SPECIALIZATION_CHOICES)[1]
            random_sexo = random.choice(CustomUser.GENDER)[1]

            user = get_user_model().objects.create_user(
                username=f'terapeuta_{i}a',
                password='1234',
                nome=names.get_full_name(),
                estado=region.name,
                cidade=city.name,
                nascimento='1990-01-01',
                telefone='123456789',
                email=f'terapeuta_{i}@example.com',
                sexo=random_sexo,
                preco=random.randint(5, 70),
                user_type='terapeuta'
            )
            user.idioma.set(random.sample(linguas, random.randint(1, len(linguas))))
            user.especialidade = random_especialidade
            user.save()
            publico_alvo_options = PublicoAlvo.objects.all()
            user.publico.set(random.sample(list(publico_alvo_options), random.randint(1, len(publico_alvo_options))))

            user = get_user_model().objects.create_user(
                username=f'paciente_{i}',
                password='1234',
                nome=names.get_full_name(),
                estado=region.name,
                cidade=city.name,
                nascimento='1990-01-01',
                telefone='123456789',
                email=f'paciente_{i}@example.com',
                sexo=random_sexo,
                user_type='paciente'
            )
            user.idioma.set(random.sample(linguas, random.randint(1, len(linguas))))
            user.save()

        self.stdout.write(self.style.SUCCESS('Successfully populated the database.'))
