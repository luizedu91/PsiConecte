from datetime import timedelta
from django.utils import timezone
from .models import *


#Function to calculate the number of appointments a therapist has in a given month. Necessary to avoid creating more appointments than their set cap.
def n_eventos_mes(data, terapeuta):
    appointment_month_start = timezone.make_aware(data.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    appointment_month_end = appointment_month_start + timedelta(days=31)
    appointment_month_end = appointment_month_end.replace(day=1)

    appointments_in_month = Evento.objects.filter(
        terapeuta=terapeuta,
        horario__gte=appointment_month_start,
        horario__lt=appointment_month_end
    ).count()

    return appointments_in_month
