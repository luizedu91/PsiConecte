from django.db import migrations

PUBLIC_ALVO = [
    ('crianca', 'Crianças'),
    ('adolescente', 'Adolescentes'),
    ('adulto', 'Adultos'),
    ('idoso', 'Idosos'),
    ('casais', 'Terapia de casal'),
    ('familia', 'Famílias'),
    ('libras', 'Libras'),
]

def create_publico_alvo(apps, schema_editor):
    PublicoAlvo = apps.get_model('app', 'PublicoAlvo')
    for _, publico in PUBLIC_ALVO:
        PublicoAlvo.objects.create(publico=publico)

def reverse_publico_alvo(apps, schema_editor):
    PublicoAlvo = apps.get_model('app', 'PublicoAlvo')
    PublicoAlvo.objects.all().delete()

def populate_linguas(apps, schema_editor):
    Linguas = apps.get_model('app', 'Linguas')
    languages = ['Inglês', 'Português', 'Espanhol', 'Francês', 'Alemão', 'Italiano', 'Mandarim', 'Russo', 'Árabe', 'Holandês']

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
