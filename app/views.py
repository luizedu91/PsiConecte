from django.utils import timezone
from django.urls import reverse
from django.utils.timezone import now
import json
#from pagseguro import PagSeguro
from django.conf import settings
from django.views.decorators.http import require_POST
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.template.loader import render_to_string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.db.models import ExpressionWrapper, fields
from django.db.models.functions import ExtractYear
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
from .models import *
from .forms import *
from .utils import *

@csrf_protect
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
            messages.error(request, 'Credenciais inválidas')
    else:  
        form = LoginForm()
        return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect(login_view)

@login_required(login_url='login')
def home(request):
    # Get the current user making the request
    user = request.user

    if user.user_type == 'terapeuta':
         # Retrieve appointments with future dates
        agendamentos = Evento.objects.filter(terapeuta_id=user.uuid, horario__gte=timezone.now()).values('id', 'terapeuta__nome', 'paciente__nome', 'horario', 'paciente__telefone', 'duracao', 'notas', 'terapeuta__preco', 'paciente__uuid')
    else:
        agendamentos = Evento.objects.filter(paciente_id=user.uuid, horario__gte=timezone.now()).values('id', 'paciente__nome', 'terapeuta__nome', 'horario', 'terapeuta__telefone', 'duracao', 'notas', 'paciente__preco', 'terapeuta__uuid')
    
    # Create the context to be passed to the template
    context = {
            'user_type':user.user_type,
            'agendamento': agendamentos,
        }
    
    # Render the home.html template with the provided context
    return render(request, 'home.html', context)

@login_required(login_url='login')
def buscar(request):
    user = request.user
    user_type = user.user_type

     # Filter by user type and set form and columns accordingly
    if user_type == 'terapeuta':
        target = CustomUser.objects.filter(user_type='paciente')
        form = SearchForm(request.GET, user=request.user, user_type=user_type)
        columns = ['Nome', 'Gênero', 'Idade', 'Idiomas', 'Estado', 'Cidade', 'Valor à disposição']
    else:
        columns = ['Nome', 'Gênero', 'Idade', 'Idiomas', 'Estado', 'Cidade', 'Linha Teórica', 'Público Alvo', 'Formação Acadêmica', 'Preço']
        target = CustomUser.objects.filter(user_type='terapeuta')
        form = SearchForm(request.GET, user=request.user, user_type=user_type)
    
    # Validate form and apply filters
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
        
        # Apply filters to target based on form data
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
        
        # Calculate age and annotate it to target
        if max_idade:
            target = target.annotate(max_idade=ExpressionWrapper(
                    current_year - max_idade - ExtractYear('nascimento'),
                    output_field=fields.IntegerField()))
            target = target.filter(nascimento__gte=now() - timedelta(days=max_idade*365.25))
        
        target = target.annotate(idade=ExpressionWrapper(
                current_year - ExtractYear('nascimento'),
                output_field=fields.IntegerField()))
        
        # Handle sorting
        sort_by = request.GET.get('sort_by', '')
        order = request.GET.get('order', '')
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
        if sort_by == 'Preço' or sort_by=='Valor à disposição':
            sort_by = 'preco'

        if sort_by and order:
            if order == 'asc':
                target = target.order_by(sort_by)
            elif order == 'desc':
                target = target.order_by('-' + sort_by)

    # Prepare context and render the template
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
            
            # Set patient and therapist and retrieve email and phone for notifications
            if user_type=='terapeuta':
                agendamento.terapeuta = user
                recipient_email = agendamento.paciente.email
                recipient_phone = agendamento.paciente.telefone
            else:
                # Checks if therapist has reached their limit to the target month
                terapeuta = CustomUser.objects.get(username=agendamento.terapeuta)
                if n_eventos_mes(agendamento.horario, terapeuta) >= terapeuta.limite_eventos:
                    messages.error(request, "Terapeuta atingiu seu limite mensal de agendamentos")
                    return redirect('agendamento')
                else:    
                    agendamento.paciente = user
                    recipient_email = agendamento.terapeuta.email
                    recipient_phone = agendamento.terapeuta.telefone
            
            # Create pending agendamento and save it
            pending_agendamento = PendingAgendamento(
                terapeuta=agendamento.terapeuta,
                paciente=agendamento.paciente,
                horario=agendamento.horario,
                notas=agendamento.notas,
                num_occurrences = form.cleaned_data['num_occurrences'])
            pending_agendamento.save()

            confirmation_token = str(pending_agendamento.confirmation_token)
            
            # Generate email and WhatsApp message content
            if user.mandar_email:
                if user_type=='terapeuta':
                    html_content = render_to_string('pedido_agendamento_terapeuta.html', {'agendamento': agendamento, 'confirmation_token': confirmation_token, 'mensagem':form.cleaned_data['mensagem']})
                else:
                    html_content = render_to_string('pedido_agendamento_paciente.html', {'agendamento': agendamento, 'confirmation_token': confirmation_token, 'mensagem':form.cleaned_data['mensagem']})
            
            '''if user.mandar_whats:
                if user_type=='terapeuta':
                    whats_content = render_to_string('pedido_agendamento_terapeuta_whats.html', {'agendamento': agendamento, 'confirmation_token': confirmation_token, 'mensagem':form.cleaned_data['mensagem']})
                else:
                    whats_content = render_to_string('pedido_agendamento_terapeuta_whats.html', {'agendamento': agendamento, 'confirmation_token': confirmation_token, 'mensagem':form.cleaned_data['mensagem']})'''
        
            text_content = strip_tags(html_content)
            msg = EmailMultiAlternatives('Pedido de Agendamento', text_content, 'psicosocialbr@yahoo.com', [recipient_email])
            msg.attach_alternative(text_content, "text/html")
            #msg.send()
            #send_whatsapp_message(recipient_phone, text_content)

            messages.success(request, "Email enviado")
            return redirect('home')
    else:
        # Initialize form and set queryset for user type
        form = AgendamentoForm(user=request.user, user_type=user_type, target_user=target_user)
        if user_type=='terapeuta':
            form.fields['terapeuta'].queryset = CustomUser.objects.filter(username=user)
            form.fields['paciente'].required = True
        else:
            form.fields['paciente'].queryset = CustomUser.objects.filter(username=user)
            form.fields['terapeuta'].required = True

    return render(request, 'agendamento.html', {'form': form})

def register_1(request):
    #First part of the registration procedure
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
            user.mandar_email = form.cleaned_data.get('mandar_email')
            user.mandar_whats = form.cleaned_data.get('mandar_whats')
            user.save()
            if user_type == 'terapeuta':
                user.especialidade = form.cleaned_data.get('especialidade')
                publico = form.cleaned_data.get('publico')
                user.formacao = form.cleaned_data.get('formacao')
                user.save()
                user.publico.set(publico)
            idioma = form.cleaned_data.get('idioma')
            user.idioma.set(idioma)
            user = authenticate(username=username, password=password1)
            login(request, user)
            return redirect('/home')
    else:
        form = RegisterForm(user_type=user_type)

    return render(request, 'register_2.html', {'form': form, 'regions': Region.objects.order_by('name')})

def get_cities(request, region_id):
    #used to populate the cities field after selecting a state
    cities = list(City.objects.filter(region_id=region_id).values())
    return JsonResponse(cities, safe=False)

def confirmado(request, confirmation_token):
    # Creates an appointment after the confirmation email is cliked. 
    pending_agendamento = get_object_or_404(PendingAgendamento, confirmation_token=confirmation_token)
    num_occurrences = pending_agendamento.num_occurrences
   
    for i in range(num_occurrences):
        pending_agendamento = Evento(
            terapeuta=pending_agendamento.terapeuta,
            paciente=pending_agendamento.paciente,
            horario=pending_agendamento.horario + timedelta(weeks=i),
            notas=pending_agendamento.notas)
        pending_agendamento.save()
        CustomUser.objects.filter(uuid=pending_agendamento.terapeuta).n_eventos += 1
    pending_agendamento.delete()

    messages.success(request, "Agendamento confirmado")
    return redirect('home')

@login_required(login_url='login')
def perfil(request, user_uuid):
    # Shows profile page
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
    new_notes = data.get('notas', '').strip()

    agendamento.notas = new_notes
    agendamento.save()

    print("atualizar notas", request, agendamento_id)

    return JsonResponse({"success": True, "notas": new_notes})

@login_required(login_url='login')
def cancelar_evento(request, agendamento_id):
    user = request.user
    evento = get_object_or_404(Evento, pk=agendamento_id)
    if request.user.has_perm('app.delete_event') == False and (str(evento.terapeuta) != str(request.user.nome) or str(evento.paciente) != str(request.user.nome)):
        return HttpResponseForbidden()
    else:
        html_content = render_to_string('cancelamento.html', {'agendamento': evento, 'self': user.nome})
        if user.user_type=="terapeuta":
            recipient_email = evento.paciente.email
        else:
            recipient_email = evento.terapeuta.email
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives('Agendamento cancelado', text_content, 'psicosocialbr@yahoo.com', [recipient_email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        evento.delete()
        messages.success(request, "Agendamento cancelado")
        return redirect('home')

@login_required(login_url='login')
def editar_perfil(request):
    if request.method == 'POST':
        form = CustomUserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            user_instance = form.save(commit=False)
            user_instance.save()
            if 'profile_picture' in request.FILES:
                user_instance.foto = request.FILES['profile_picture']
                user_instance.save()
            return redirect('perfil', user_uuid=request.user.uuid)

    else:
        form = CustomUserUpdateForm(instance=request.user)
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

def eventos_json(request):
    event_list = []
    user = request.user
    if user.user_type=='terapeuta':
        agendamentos = Evento.objects.filter(terapeuta_id=user.uuid)
        for i in agendamentos:
            dt = i.horario
            event_list.append({
                'user_type': user.user_type,
                 'title': i.paciente.nome, 
                 'target': {
                    'uuid': str(i.paciente.uuid),
                    'nome': i.paciente.nome,
                    'telefone': i.paciente.telefone,
                },
                'allDay': False, 
                'event_id':i.id,
                'start': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M'),
                'notas': str(i.notas)
            })
    else:   
        agendamentos = Evento.objects.filter(paciente_id=user.uuid)
        for i in agendamentos:
            dt = i.horario
            event_list.append({
                'event_id':i.id,
                'user_type': user.user_type,
                'title': i.terapeuta.nome,
                'target': {
                    'uuid': str(i.terapeuta.uuid),
                    'nome': i.terapeuta.nome,
                    'telefone': i.terapeuta.telefone,
                },
                'allDay': False, 
                'start': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M:%S'), 
            })
            
    return JsonResponse(event_list, safe=False)

'''def send_whatsapp_message(recipient_phone_number, message_body):

    messenger = WhatsApp('EAADg345gtEkBADoS12Q7d9f0MUNkZCXjYLmKfL5e5yrOLSm9IDvqz6krOYW7zDVgkF4O5dNMCOfIflrAboxOwoyYQ9ncT6rXr91ptkvvZAiHQqtvnHI2kgyoQF5Dwm3BTmDpJwunmq5CgIvsdIRfqeUziZARLruu0rGbhZByey7gUyXC3xhxlwWZAyczLBO9EUw0bWtMS5GpVJhSVRcWWpkMYZB0FvZCCWj06mOdSC4ywZDZD',  phone_number_id='114845358238519')
    messenger.send_message(message_body, "+55"+recipient_phone_number)'''

@csrf_exempt 
def available_terapeutas(request):
    selected_date = datetime.strptime(request.GET.get('selected_date', '').split("T")[0],'%Y-%m-%d')
    terapeutas = CustomUser.objects.filter(user_type='terapeuta')
    available_terapeutas = []
    for terapeuta in terapeutas:
        if n_eventos_mes(selected_date, terapeuta) < terapeuta.limite_eventos:
            available_terapeutas.append(terapeuta)
    terapeutas_data = [{'uuid': str(terapeuta.uuid), 'nome': terapeuta.nome} for terapeuta in available_terapeutas]
    return JsonResponse(terapeutas_data, safe=False)

'''def create_checkout(request):
    if request.method == "POST":
        try:
            pag = PagSeguro(
                email=settings.PAGSEGURO_EMAIL,
                token=settings.PAGSEGURO_TOKEN,
                config={'sandbox': settings.PAGSEGURO_SANDBOX}
            )

            pag.items.append({
                'id': '1',
                'description': 'Appointment Booking',
                'amount': '10.00',  # Set the appointment price here
                'quantity': '1'
            })

            pag.redirect_url = 'your_success_url'  # Set your success URL
            pag.notification_url = 'your_notification_url'  # Set your notification URL for receiving status updates

            response = pag.checkout()

            if response.status == 200:
                return JsonResponse({'redirect_url': response.payment_url})
            else:
                return JsonResponse({'error': 'PagSeguro checkout error'})
        except Exception as e:
            return JsonResponse({'error': str(e)})
    return JsonResponse({'error': 'Invalid request method'})'''