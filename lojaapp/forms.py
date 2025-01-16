from django import forms
from .models import Pedido_order,Cliente
from django.forms import ModelForm, TextInput, EmailInput
from django.contrib.auth.models import User



class Checar_PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido_order
        fields = ["ordenando_por", "endereco_envio", "telefone", "email","pagamento_method"]


class ClienteRegistrarForm(forms.ModelForm):
    usuario = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Usuario', 'class': "form-control", 'style': 'width:300px;display: flex;'}))
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Sua Senha', 'class': "form-control", 'style': 'width:300px;display: flex;'}))
    email = forms.CharField(widget=forms.EmailInput(attrs={'placeholder':'Seu Email', 'class': "form-control", 'style': 'width:300px;display: flex;'}))
    class Meta:
        model = Cliente
        fields = ["usuario", "senha", "email", "nome_completo", "endereco"]
        
        def clean_username(self):
            unome = self.cleaned_data.get("usuario")
            if User.objects.filter(username=unome).exists():
                raise forms.ValidationError("ESTE CLIENTE JA EXISTE NO BANCO DE DADOS")
            return unome

class ClienteEntrarForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())
