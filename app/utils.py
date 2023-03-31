from datetime import timedelta
from django.db.models import Count
from .models import *
from django.core.exceptions import ValidationError

def terapeutas_disponiveis(queryset, data):
    terapeutas_disponiveis = []
    for terapeuta in queryset:
        if contar_eventos(terapeuta, data) < terapeuta.limite_eventos:
            terapeutas_disponiveis.append(terapeuta) 
    return terapeutas_disponiveis

def contar_eventos(terapeuta, datetime):
    start_date = datetime.replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1)
    return Evento.objects.filter(terapeuta=terapeuta, date__range=(start_date, end_date)).count()
