from django import forms
from .models import *
from django.forms import widgets
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm, PasswordChangeForm
from crispy_forms.layout import Layout, Submit, Button, Row, Column
from crispy_bootstrap5.bootstrap5 import FloatingField, Field
from django.core.validators import MinValueValidator,MaxValueValidator
from django.contrib.auth import get_user_model
from django.forms import ModelMultipleChoiceField
from crispy_forms.helper import FormHelper



class RegionChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.name

class UserTypeForm(forms.Form):
    user_type = forms.ChoiceField(choices=[('terapeuta', 'Terapeuta'), ('paciente', 'Paciente')], widget=forms.RadioSelect)
    username = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(required=True, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    def __init__(self, *args, **kwargs):
        super(UserTypeForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.fields['password1'].label = 'Senha'
        self.fields['password1'].help_text = None
        self.fields['password2'].label = 'Confirme a nova senha'
        self.fields['password2'].help_text = None
        self.helper.add_input(Submit('submit', 'Salvar', css_class='btn btn-primary'))
        self.helper.layout = Layout(
            Row(
            Column(FloatingField('username', css_class='form-control mb-3')),
            Column(FloatingField('email', css_class='form-control mb-3'))),
            Row(
            Column(FloatingField('password1', css_class='form-control mb-3')),
            Column(FloatingField('password2', css_class='form-control mb-3'))
            ))
        self.error_messages = {
            'password_incorrect': _("Senha atual incorreta. Por favor, insira novamente."),
            'password_mismatch': _("As senhas não coincidem."),
            'password_too_short': _("A senha é muito curta."),
            'password_too_common': _("A senha é muito comum."),
            'password_entirely_numeric': _("A senha não pode ser inteiramente numérica."),
            'password_incorrect': _("Senha atual incorreta. Por favor, insira novamente."),
        }

class RegisterForm(forms.ModelForm):
    nome = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    nascimento = forms.DateField(required=True, input_formats=['%d/%m/%Y'], widget=forms.DateInput(attrs={'class': 'form-control', 'id': 'id_nascimento'}))
    telefone = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cidade = forms.ModelChoiceField(queryset=City.objects.all().order_by('name'), required=False, label='Cidade', widget=forms.Select(attrs={'class': 'form-select'}))
    estado = RegionChoiceField(queryset=Region.objects.all().order_by('name'), required=True, label='Estado', widget=forms.Select(attrs={'class': 'form-select'}))
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'id': 'bio-field'}), required=False, )
    preco = forms.DecimalField(max_digits=20, decimal_places=2, required=False, label='Preço', validators=[MinValueValidator(0),MaxValueValidator(100)], widget=forms.NumberInput(attrs={'class': 'form-control', 'step':'5', 'id': 'preco-widget'}))
    sexo = forms.ChoiceField(choices=CustomUser.GENDER, required=True, label='Sexo', widget=forms.Select(attrs={'class': 'form-select'}))
    idioma = ModelMultipleChoiceField(queryset=Linguas.objects.all(), label='Idioma de preferência', required=False, widget=forms.SelectMultiple(attrs={'class': 'form-select'}))
    profile_picture = forms.ImageField(required=False, label="Foto do perfil", widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    especialidade = forms.ChoiceField(choices=CustomUser.SPECIALIZATION_CHOICES, required=False, label='Linha Teórica', widget=forms.Select(attrs={'class': 'form-select'}))
    publico = ModelMultipleChoiceField(queryset=PublicoAlvo.objects.all(), required=False, widget=forms.SelectMultiple(attrs={'class': 'form-select'}))
    formacao = forms.CharField(max_length=100, required=False, label='Formação Acadêmica', widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        exclude = ('password1', 'password2') 
        fields = ('nome', 'nascimento', 'telefone', 'estado', 'cidade', 'bio', 'preco', 'sexo', 'idioma', 'profile_picture', 'especialidade', 'publico', 'formacao')
    
    def __init__(self, user_type=None, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        self.user_type = user_type
        self.helper = FormHelper()
        self.helper.form_method = 'post'

        common_fields = [
                FloatingField('nome', css_class='form-group-sm mb-3'),
                Field('bio', css_class='form-group-sm mb-3'),
            Row(
                Column(FloatingField('nascimento', css_class='form-group-sm col-md-2 mb-3')),
                Column(FloatingField('sexo', css_class='form-group-sm col-md-2 mb-3')),
                Column(FloatingField('telefone', css_class='form-group-sm col-md-2 mb-3')),
            ),
            Row(
                Column(FloatingField('estado', css_class='form-group-sm col-md-6 mb-3')),
                Column(FloatingField('cidade', css_class='form-group-sm col-md-6 mb-3')),
            ),
            Row(
                Column(Field('idioma', css_class='form-group-sm col-md-3 mb-3 js-select2')),
                Column(Field('preco', css_class='form-group-sm col-md-3 mb-3')),
                Column(Field('profile_picture', css_class='form-group-sm col-md-3 mb-3')),
            )
        ]
                
        terapeuta_fields = [
            Row(
        Column(Field('especialidade', css_class='form-group-sm mb-3'), css_class='col-md-4'),
        Column(Field('publico', css_class='form-group-sm mb-3 js-select2'), css_class='col-md-4'),
        Column(Field('formacao', css_class='form-group-sm mb-3'), css_class='col-md-4'),
    ),]

        if user_type == 'terapeuta':
            layout_fields = common_fields + terapeuta_fields
            self.fields['preco'].label = 'Preço de sua consulta. Valor entre R$ 5 e R$70'
            self.fields['bio'].label = 'Conte um pouco sobre você e seu trabalho'
            self.fields['idioma'].label='Idiomas'
        else:
            layout_fields = common_fields
            self.fields['preco'].label = 'Valor que está disposto a pagar por uma consulta. Valor entre R$ 5 e R$70'
            self.fields['bio'].label = 'Conte pouco sobre você e seu histórico de saúde mental. Importante mencionar se toma algum medicamento.'
            self.fields['idioma'].label='Idioma de preferência'

        self.helper.layout = Layout(*layout_fields)
        self.helper.add_input(Submit('submit', 'Registrar', css_class='btn btn-primary btn-lg'))
        self.helper.add_input(Button('cancel', 'Cancelar', css_class='btn btn-outline-secondary btn-lg'))

class SearchForm(forms.Form):
    cidade = forms.ModelChoiceField(queryset=City.objects.none(), required=False, label='Cidade', widget=forms.Select(attrs={'class': 'form-select'}))
    estado = RegionChoiceField(queryset=Region.objects.all().order_by('name'), required=False, label='Estado', widget=forms.Select(attrs={'class': 'form-select'}))
    max_preco = forms.DecimalField(max_digits=20, decimal_places=0, required=False, label='Valor máximo R$', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    especialidade = forms.ChoiceField(choices= [('', '-----')] + CustomUser.SPECIALIZATION_CHOICES, required=False, label='Linha Teórica', widget=forms.Select(attrs={'class': 'form-select ','data-placeholder': ''}))
    sexo = forms.ChoiceField(choices=[('', '-----')] + CustomUser.GENDER, required=False, label='Gênero', widget=forms.Select(attrs={'class': 'form-select', 'data-placeholder': ''}))
    min_idade = forms.IntegerField(required=False, label="Idade mínima", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    max_idade = forms.IntegerField(required=False, label="Idade máxima", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    idioma = forms.ModelMultipleChoiceField(queryset=Linguas.objects.all(), required=False, label='Idiomas', widget=forms.SelectMultiple(attrs={'class': 'form-select ', 'data-placeholder': ''}))
    publico = forms.ModelMultipleChoiceField(queryset=PublicoAlvo.objects.all(), required=False, label='Público Alvo', widget=forms.SelectMultiple(attrs={'class': 'form-select', 'data-placeholder': ''}))
    formacao = forms.CharField(required=False, label='Formação Acadêmica', widget=forms.TextInput(attrs={'class': 'form-control'}))


    def __init__(self, *args, user, user_type, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.user = user
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column(FloatingField('estado', css_class='form-group-sm col-md-2 mb-3')),
                Column(FloatingField('cidade', css_class='form-group-sm col-md-2 mb-3')),
                Column(FloatingField('sexo', css_class='form-group-sm col-md-3 mb-3')),
            ),
            Row(
                Column(FloatingField('min_idade', css_class='form-group-sm col-md-1 mb-3')),
                Column(FloatingField('max_idade', css_class='form-group-sm col-md-1 mb-3')),
                Column(FloatingField('max_preco', css_class='form-group-sm col-md-2 mb-3')),
                Column(FloatingField('especialidade', css_class='form-group-sm col-md-3 mb-3'))
            ),
            Row(
                Column(Field('idioma', css_class='form-group col-md-4 mb-3 js-select2')),
                Column(Field('publico', css_class='form-group col-md-4 mb-3 js-select2')),
            )
        )
        self.helper.add_input(Submit('submit', 'Buscar', css_class='btn btn-primary btn-lg'))
        if user_type == 'terapeuta':
            self.fields['especialidade'].initial = None
            self.fields['especialidade'].widget = forms.HiddenInput()
            self.fields['publico'].initial = None
            self.fields['publico'].widget = forms.HiddenInput()
            self.fields['formacao'].initial = None
            self.fields['formacao'].widget = forms.HiddenInput()

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), label="Nome de usuário ")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Senha ')

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Enviar', css_class='btn-primary'))
        self.helper.layout = Layout(
            FloatingField('username', placeholder='Username'),
            FloatingField('password', placeholder='Password'),
            )
        
class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nome
class AgendamentoForm(forms.ModelForm):
    terapeuta = UserModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='terapeuta'),
        label='Terapeuta',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}))
    paciente = UserModelChoiceField(
        queryset=CustomUser.objects.filter(user_type='paciente'),
        label='Paciente',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}))
    horario = forms.DateTimeField(
        label='Horario',
        input_formats=['%d/%m/%Y %H:%M'],
        widget=widgets.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%d/%m/%Y T%H:%M'))
    
    duracao = forms.IntegerField(label='Duração', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    mensagem = forms.CharField(required=False, label="Mensagem", widget=forms.Textarea)
    nota = forms.CharField(required=False, label="Notas privadas", widget=forms.Textarea)

    def __init__(self, *args, target_user=None, user_type, user, **kwargs):
        super(AgendamentoForm, self).__init__(*args, **kwargs)
        self.user = user
        self.helper = FormHelper()
        if user_type == 'terapeuta':
            self.fields['terapeuta'].initial = self.user
            self.fields['paciente'].initial = target_user
            self.fields['paciente'].required = True
            self.helper.layout = Layout(
            Row(
                Column(FloatingField('paciente', css_class='form-group col-md-8 mb-3')),
                Column(FloatingField('horario', css_class='form-group-sm col-md-2 mb-3')),
                Column(FloatingField('duracao', css_class='form-group-sm col-md-1 mb-3'))),
            Row(
                Column(FloatingField('mensagem', css_class='form-group-sm col-md-4 mb-3')),
                Column(FloatingField('nota', css_class='form-group-sm col-md-4 mb-3'))))
        elif user_type == 'paciente':
            self.fields['paciente'].initial = self.user
            self.fields['terapeuta'].initial = target_user
            self.fields['terapeuta'].required = True
            self.fields['paciente'].initial = self.user
            self.helper.layout = Layout(
            Row(
                Column(FloatingField('terapeuta', css_class='form-group col-md-8 mb-3')),
                Column(FloatingField('horario', css_class='form-group-sm col-md-2 mb-3'))),
            Row(
                Column(FloatingField('mensagem', css_class='form-group-sm col-md-4 mb-3'))))
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Enviar', css_class='btn-primary'))

    class Meta:
        model = Evento
        fields = ['terapeuta', 'paciente', 'horario', 'duracao', 'mensagem', 'nota']

class CustomUserUpdateForm(UserChangeForm):
    cidade = forms.ModelChoiceField(queryset=City.objects.all().order_by('name'), required=False, label='Cidade', widget=forms.Select(attrs={'class': 'form-select'}))
    estado = RegionChoiceField(queryset=Region.objects.all().order_by('name'), required=False, label='Estado', widget=forms.Select(attrs={'class': 'form-select'}))
    profile_picture = forms.ImageField(required=False, label="Profile Picture")
    idiomas = forms.ModelMultipleChoiceField(queryset=Linguas.objects.all(), required=False, label='Idiomas', widget=forms.SelectMultiple(attrs={'class': 'form-select'}))
    preco = forms.DecimalField(max_digits=20, decimal_places=2, required=False, label='Preço', validators=[MinValueValidator(0)], widget=forms.NumberInput(attrs={'class': 'form-control'}))
    especialidade = forms.ChoiceField(choices=CustomUser.SPECIALIZATION_CHOICES, required=False, label='Linha Teórica', widget=forms.Select(attrs={'class': 'form-select'}))
    publico = ModelMultipleChoiceField(queryset=PublicoAlvo.objects.all(), label='Público Alvo', required=False, widget=forms.SelectMultiple(attrs={'class': 'form-select'}))
    formacao = forms.CharField(max_length=100, required=False, label='Formação Acadêmica', widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ('telefone', 'email',  'estado', 'cidade',  'bio', 'idiomas', 'especialidade', 'publico', 'preco')

    def __init__(self, user_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Enviar', css_class='btn-primary'))
        self.helper.layout = Layout(
        FloatingField('telefone', css_class='form-control mb-3'),
        FloatingField('email', css_class='form-control mb-3'),
        FloatingField('estado', css_class='form-select mb-3'),
        FloatingField('cidade', css_class='form-control mb-3'),
        FloatingField('bio', css_class='form-control mb-3'),
        Field('idiomas', css_class='form-select mb-3 js-select2'),
        Field('especialidade', css_class='form-control mb-3'),
        Field('publico', css_class='form-select mb-3 js-select2'),
        FloatingField('preco', css_class='form-control mb-3'),
        FloatingField('formacao', css_class='form-control mb-3'))
        self.fields['password'].widget = forms.HiddenInput()
        if user_type == 'paciente':
            self.fields['publico'].widget = forms.HiddenInput()
            self.fields['especialidade'].widget = forms.HiddenInput()
            self.fields['formacao'].widget = forms.HiddenInput()            
            self.fields['bio'].label = 'Conte pouco sobre você e seu histórico de saúde mental. Importante mencionar se toma algum medicamento.'
            self.fields['preco'].label = 'Valor que está disposto a pagar por uma consulta. Valor entre R$ 5 e R$70'
        else:
            self.fields['preco'].label = 'Preço de sua consulta. Valor entre R$ 5 e R$70'
            self.fields['bio'].label = 'Conte um pouco sobre você e seu trabalho'

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label=_("Senha atual"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )

    new_password1 = forms.CharField(
        label=_("Nova senha"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )

    new_password2 = forms.CharField(
        label=_("Confirme a nova senha"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Salvar', css_class='btn btn-primary'))
        self.fields['old_password'].label = 'Senha antiga'
        self.fields['new_password1'].label = 'Nova senha'
        self.fields['new_password1'].help_text = None
        self.fields['new_password2'].label = 'Confirme a nova senha'
        self.helper.layout = Layout(
            FloatingField('old_password', wrapper_class='col-md-6 mb-3'),
            FloatingField('new_password1', wrapper_class='col-md-6 mb-3'),
            FloatingField('new_password2', wrapper_class='col-md-6 mb-3'),
            )
        
        self.error_messages = {
            'password_incorrect': _("Senha atual incorreta. Por favor, insira novamente."),
            'password_mismatch': _("As senhas não coincidem."),
            'password_too_short': _("A senha é muito curta."),
            'password_too_common': _("A senha é muito comum."),
            'password_entirely_numeric': _("A senha não pode ser inteiramente numérica."),
            'password_incorrect': _("Senha atual incorreta. Por favor, insira novamente."),
        }