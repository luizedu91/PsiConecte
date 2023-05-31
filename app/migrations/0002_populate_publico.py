from django.db import migrations

PUBLIC_ALVO = ['Crianças','Adolescentes','Adultos','Idosos','Terapia de casal','Famílias','Libras', 'Ansiedade', 'Depressão', 'Alterações de humor', 'Acompanhamento psicológico', 'Estresse']

def create_publico_alvo(apps, schema_editor):
    PublicoAlvo = apps.get_model('app', 'PublicoAlvo')
    for publico in PUBLIC_ALVO:
        PublicoAlvo.objects.create(publico=publico)

def reverse_publico_alvo(apps, schema_editor):
    PublicoAlvo = apps.get_model('app', 'PublicoAlvo')
    PublicoAlvo.objects.all().delete()

def populate_linguas(apps, schema_editor):
    Linguas = apps.get_model('app', 'Linguas')
    languages = [
     'Português','Inglês', 'Espanhol', 'Francês', 'Alemão',  'Mandarim','Italiano', 'Árabe', 'Holandês',
    'Japonês', 'Coreano', 'Sueco', 'Norueguês', 'Dinamarquês', 'Finlandês', 'Turco', 'Grego', 'Hebraico', 'Húngaro',
    'Tailandês', 'Checo', 'Polonês', 'Romeno', 'Búlgaro', 'Croata', 'Eslovaco', 'Esloveno', 'Ucraniano', 'Catalão',
    'Bengali', 'Hindi', 'Urdu', 'Gujarati', 'Marathi', 'Tâmil', 'Telugu', 'Malaiala', 'Tagalo', 'Vietnamita', 'Indonésio', 'Malaio', 'Swahili', 'Islandês', 'Russo', 'Gaélico Escocês', 'Galês',
    'Basco', 'Estoniano', 'Letão', 'Lituano', 'Maltês', 'Albanês', 'Armênio', 'Georgiano', 'Persa', 'Sérvio',
    'Macedônio', 'Bielorrusso', 'Bósnio', 'Cazaque', 'Uzbeque', 'Azerbaijano', 'Turcomeno', 'Quirguiz', 'Tajique',
    'Afrikaans', 'Yoruba', 'Zulu', 'Xhosa', 'Somali', 'Amárico', 'Quechua', 'Havaiano', 'Maori', 'Samoano', 'Tonganês',
    'Cherokee', 'Navajo', 'Inuktitut', 'Esperanto']

    for language in languages:
        Linguas.objects.create(linguas=language)

class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_publico_alvo, reverse_publico_alvo),
        migrations.RunPython(populate_linguas),
    ]
