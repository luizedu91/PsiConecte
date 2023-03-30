from django.utils import timezone
from django.urls import reverse
from django.utils.timezone import now
import json
from django.views.decorators.http import require_POST
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from datetime import date, timedelta
from django.db.models import F, ExpressionWrapper, fields
from django.db.models.functions import ExtractYear
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from .models import *
from .forms import *

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('/')
        else:
            return render(request, 'login.html', {'form': form, 'error_message': 'Invalid login credentials'})
    else:  
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect(login_view)

@login_required(login_url='login')
def home(request):
    user = request.user
    user_type = 'terapeuta' if user.is_terapeuta else 'paciente'
    if user_type == 'terapeuta':
        agendamentos = Evento.objects.filter(terapeuta_id=user.uuid, horario__gte=timezone.now()).values('id', 'terapeuta__nome', 'paciente__nome', 'horario', 'paciente__telefone', 'duracao', 'notas', 'terapeuta__preco', 'paciente__uuid')

    else:
        agendamentos = Evento.objects.filter(paciente_id=user.uuid, horario__gte=timezone.now()).values('id', 'paciente__nome', 'terapeuta__nome', 'horario', 'terapeuta__telefone', 'duracao', 'notas', 'paciente__preco', 'terapeuta__uuid')

    context = {
            'user_type':user_type,
            'agendamentos': agendamentos,
        }
    return render(request, 'home.html', context)

@login_required(login_url='login')
def buscar(request):
    user = request.user
    is_terapeuta = hasattr(user, 'terapeuta')

    if is_terapeuta:
        user_type = 'terapeuta'
        target = CustomUser.objects.filter(user_type='paciente')
        form = SearchForm(request.GET, user=request.user, user_type=user_type)
        columns = ['Nome', 'Gênero', 'Idade', 'Idiomas', 'Estado', 'Cidade', 'Preço']

    else:
        columns = ['Nome', 'Gênero', 'Idade', 'Idiomas', 'Estado', 'Cidade', 'Linha Teórica', 'Público Alvo', 'Formação Acadêmica', 'Preço']
        user_type = 'paciente'
        target = CustomUser.objects.filter(user_type='terapeuta')
        form = SearchForm(request.GET, user=request.user, user_type=user_type)

    if form.is_valid():
        cidade = form.cleaned_data.get('cidade')
        estado = form.cleaned_data.get('estado')
        max_preco = form.cleaned_data.get('max_preco')
        especialidade = form.cleaned_data.get('especialidade')
        sexo = form.cleaned_data.get('sexo')
        idioma = form.cleaned_data.get('idioma')
        publico = form.cleaned_data.get('publico')
        formacao = form.cleaned_data.get('formacao')
        min_idade = form.cleaned_data.get('min_idade')
        max_idade = form.cleaned_data.get('max_idade')
        current_year = date.today().year

        if cidade:
            target = target.filter(cidade__icontains=cidade.name)
        elif estado:
            target = target.filter(estado__icontains=estado.name)
        if max_preco is not None:
            target = target.filter(preco__lte=max_preco)
        if especialidade and user_type == 'paciente':
            target = target.filter(especialidade__icontains=especialidade)
        if sexo:
            target = target.filter(sexo=sexo)
        if idioma:
            target = target.filter(idioma__linguas__in=[idioma[0]])
        if publico:
            target = target.filter(publico__publico__in=[publico[0]])
        if formacao:
            target = target.filter(formacao__icontains=formacao)
        if min_idade:
            target = target.annotate(birth_year=ExtractYear('nascimento'))
            target = target.filter(nascimento__lte=now() - timedelta(days=min_idade*365.25))
        if max_idade:
            target = target.annotate(max_idade=ExpressionWrapper(
                    current_year - max_idade - ExtractYear('nascimento'),
                    output_field=fields.IntegerField()))
            target = target.filter(nascimento__gte=now() - timedelta(days=max_idade*365.25))
        
        target = target.annotate(idade=ExpressionWrapper(
                current_year - ExtractYear('nascimento'),
                output_field=fields.IntegerField()))

        sort_by = request.GET.get('sort_by', '')
        order = request.GET.get('order', '')

#Fix sorting of fields
        if sort_by == 'Nome':
            sort_by = 'nome'
        if sort_by == 'Gênero':
            sort_by = 'sexo'
        if sort_by == 'Idade':
            sort_by = 'nascimento'
        if sort_by == 'Idiomas':
            sort_by = 'idioma'
        if sort_by == 'Cidade':
            sort_by = 'cidade'
        if sort_by == 'Estado':
            sort_by = 'estado'
        if sort_by == 'Linha Teórica':
            sort_by = 'especialidade'
        if sort_by == 'Público Alvo':
            sort_by = 'publico'
        if sort_by == 'Formação Acadêmica':
            sort_by = 'formacao'
        if sort_by == 'Preço':
            sort_by = 'preco'

        if sort_by and order:
            if order == 'asc':
                target = target.order_by(sort_by)
            elif order == 'desc':
                target = target.order_by('-' + sort_by)

    states = Region.objects.order_by('name')
    context = {
        'regions': states,
        'target': target,
        'form': form,
        'columns': columns,
        'sort_by': sort_by,
        'order': order,
        'user_type': user_type,
    }

    return render(request, 'busca.html', context)

@login_required(login_url='login')
def agendamento(request, uuid=None):
    user = request.user
    user_type=user.user_type
    target_user = None
    if uuid:
        target_user = get_object_or_404(CustomUser, uuid=uuid)

    if request.method == "POST":
        form = AgendamentoForm(request.POST, user_type=user_type, user=request.user, target_user = target_user)
        if form.is_valid():
            agendamento = form.save(commit=False)
           
            if user_type=='terapeuta':
                terapeuta = user
                paciente = form.cleaned_data['paciente']
                agendamento.terapeuta = user
                recipient_email = agendamento.paciente.email
            else:
                terapeuta = form.cleaned_data['terapeuta']
                paciente = user
                agendamento.paciente = user
                recipient_email = agendamento.terapeuta.email
    
            pending_agendamento = PendingAgendamento(
            terapeuta=terapeuta,
            paciente=paciente,
            horario=form.cleaned_data['horario'],
            notas=form.cleaned_data['nota'])

            pending_agendamento.save()
            confirmation_token = str(pending_agendamento.confirmation_token)

            html_content = render_to_string('pedido_agendamento.html', {'agendamento': agendamento, 'confirmation_token': confirmation_token, 'mensagem':form.cleaned_data['mensagem']})
            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives('Pedido de Agendamento', text_content, 'luizedu.andrade@gmail.com', [recipient_email])
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            messages.success(request, "Email enviado")
            return redirect('home')
    else:
        form = AgendamentoForm(user=request.user, user_type=user_type, target_user=target_user)
        if user_type=='terapeuta':
            form.fields['terapeuta'].queryset = CustomUser.objects.filter(username=user)
            form.fields['paciente'].required = True
        else:
            form.fields['paciente'].queryset = CustomUser.objects.filter(username=user)
            form.fields['terapeuta'].required = True

    return render(request, 'agendamento.html', {'form': form})

def register_1(request):
    if request.method == "POST":
        form = UserTypeForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['user_type']
            request.session['user_type'] = user_type
            request.session['email'] = form.cleaned_data['email']
            request.session['username'] = form.cleaned_data['username']
            request.session['password1'] = form.cleaned_data['password1']
            request.session['password2'] = form.cleaned_data['password2']
            return HttpResponseRedirect(reverse('register_2'))
        else:
            print("Form errors:", form.errors)  
        
    else:
        form = UserTypeForm()
    return render(request, 'register_1.html', {'form': form})
    
def register_2(request):
    user_type = request.session.get('user_type')
    if user_type is None:
        return HttpResponseRedirect(reverse('register'))

    if request.method == 'POST':
        email = request.session.get('email')
        username = request.session.get('username')
        password1 = request.session.get('password1')
        form = RegisterForm(data=request.POST, user_type=user_type)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = username
            user.email = email
            user.user_type = user_type
            user.set_password(password1)
            user.bio = form.cleaned_data.get('bio')
            user.nome = form.cleaned_data.get('nome')
            user.nascimento = form.cleaned_data.get('nascimento')
            user.telefone = form.cleaned_data.get('telefone') 
            user.estado = form.cleaned_data.get('estado').name
            user.cidade = form.cleaned_data.get('cidade').name
            user.preco = form.cleaned_data.get('preco')
            user.sexo = form.cleaned_data.get('sexo')
            user.save()
            if user_type == 'terapeuta':
                user.especialidade = form.cleaned_data.get('especialidade')
                publico = form.cleaned_data.get('publico')
                user.formacao = form.cleaned_data.get('formacao')
                user.save()
                user.publico.set(publico)
            idioma = form.cleaned_data.get('idioma')
            user.idioma.set(idioma)
            return redirect('/home')
    else:
        form = RegisterForm(user_type=user_type)

    return render(request, 'register_2.html', {'form': form, 'regions': Region.objects.order_by('name')})

def get_cities(request, region_id):
    cities = list(City.objects.filter(region_id=region_id).values())
    return JsonResponse(cities, safe=False)

def confirmado(request, confirmation_token):
    pending_agendamento = get_object_or_404(PendingAgendamento, confirmation_token=confirmation_token)
    
    agendamento = Evento(
        terapeuta=pending_agendamento.terapeuta,
        paciente=pending_agendamento.paciente,
        horario=pending_agendamento.horario,
        notas=pending_agendamento.notas)
    agendamento.save()
    pending_agendamento.delete()

    messages.success(request, "Agendamento confirmado")
    return redirect('home')

@login_required(login_url='login')
def perfil(request, user_uuid):
    user = get_object_or_404(CustomUser, uuid=user_uuid)
    context = {
        'user': user,
    }
    return render(request, 'perfil.html', context)

@require_POST
def atualizar_notas(request, agendamento_id):
    try:
        agendamento = Evento.objects.get(pk=agendamento_id)
    except Evento.DoesNotExist:
        return JsonResponse({"error": "Agendamento não encontrado"}, status=404)

    data = json.loads(request.body)
    new_notes = data.get('notes', '').strip()

    agendamento.notes = new_notes
    agendamento.save()

    return JsonResponse({"success": True, "notes": new_notes})

@login_required(login_url='login')
def cancelar_evento(request, agendamento_id):
    evento = get_object_or_404(Evento, pk=agendamento_id)
    if request.user.has_perm('app.delete_event') == False and (str(evento.terapeuta) != str(request.user.nome) or str(evento.paciente) != str(request.user.nome)):
        return HttpResponseForbidden()
    evento.delete()
    return redirect('home')

@login_required(login_url='login')
def editar_perfil(request):
    user_type=request.user.user_type
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('perfil', user_uuid=request.user.uuid)
    else:
        form = CustomUserUpdateForm(instance=request.user, user_type=user_type)
        return render(request, 'editar_perfil.html', {'form': form})

@login_required(login_url='login')  
def custom_password_change(request): 
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user) 
            messages.success(request, 'Sua senha foi alterada com sucesso.')
            return redirect('/home')
        else:
            messages.error(request, 'Houve um erro ao tentar alterar a senha.')
            for field in form.errors:
                messages.error(request, f"{field}: {', '.join(form.errors[field])}")
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, 'mudar_senha.html', {'form': form})



''' for debugging
for attr in dir(user):
    if not attr.startswith('_'):
        try:
            value = getattr(user, attr)
            if not isinstance(value, (models.Manager, property)):
                print(f"{attr}: {value}")
        except AttributeError:
            pass'''

