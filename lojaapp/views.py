from django.shortcuts import render, redirect
from django.views.generic import View, TemplateView, CreateView, FormView,DetailView, ListView
from django.urls import reverse_lazy, reverse
from .forms import Checar_PedidoForm, ClienteRegistrarForm, ClienteEntrarForm
from .models import *
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


def contato_view(request):
    if request.method == 'POST':
        # Simular um erro no envio
        messages.error(request, 'Ocorreu um erro ao enviar sua mensagem. Por favor, tente novamente mais tarde.')
    return render(request, 'contato.html')


class LojaMixin(object):
    def dispatch(self, request, *args, **kwargs):
        carro_id = request.session.get("carro_id")
        if carro_id:
            try:
                carro_obj = Carro.objects.get(id=carro_id)
                if request.user.is_authenticated and hasattr(request.user, 'cliente'):
                    if request.user.cliente:
                        carro_obj.cliente = request.user.cliente
                        carro_obj.save()
            except Carro.DoesNotExist:
                del request.session["carro_id"]
            except AttributeError:
                pass
        return super().dispatch(request, *args, **kwargs)


class HomeView(LojaMixin, TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_produtos = Produto.objects.all().order_by("-id")
        paginator = Paginator(all_produtos,4)
        page_number = self.request.GET.get('page')
        produto_list = paginator.get_page(page_number)
        context['produto_list'] = produto_list
        return context


class TodosProdutosView(LojaMixin, TemplateView):
    template_name = "todosprodutos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['todoscategorias'] = Categoria.objects.all()
        return context


class ProdutoDetalheView(LojaMixin, TemplateView):
    template_name = "produtodetalhe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_slug = self.kwargs['slug']
        produto = Produto.objects.get(slug=url_slug)
        produto.visualizacao += 1
        produto.save()
        context['produto'] = produto
        return context


class AddCarroView(LojaMixin, TemplateView):
    template_name = "addprocarro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        produto_id = self.kwargs['pro_id']
        produto_obj = Produto.objects.get(id=produto_id)
        carro_id = self.request.session.get("carro_id", None)
        if carro_id:
            carro_obj = Carro.objects.get(id=carro_id)
            produto_no_carro = carro_obj.carroproduto_set.filter(produto=produto_obj)

            if produto_no_carro.exists():
                carroproduto = produto_no_carro.last()
                carroproduto.quantidade += 1
                carroproduto.subtotal += produto_obj.venda
                carroproduto.save()
                carro_obj.total += produto_obj.venda
                carro_obj.save()

            else:
                carroproduto = CarroProduto.objects.create(
                    carro=carro_obj, produto=produto_obj,
                    avaliacao=produto_obj.venda, quantidade=1, subtotal=produto_obj.venda
                )
                carro_obj.total += produto_obj.venda
                carro_obj.save()
        else:
            carro_obj = Carro.objects.create(total=0)
            self.request.session['carro_id'] = carro_obj.id
            carroproduto = CarroProduto.objects.create(
                carro=carro_obj, produto=produto_obj,
                avaliacao=produto_obj.venda, quantidade=1, subtotal=produto_obj.venda
            )
            carro_obj.total += produto_obj.venda
            carro_obj.save()
        return context


class ManipularCarroView(LojaMixin, View):
    def get(self, request, *args, **kwargs):
        cp_id = self.kwargs["cp_id"]
        acao = request.GET.get("acao")
        cp_obj = CarroProduto.objects.get(id=cp_id)
        carro_obj = cp_obj.carro

        if acao == "inc":
            cp_obj.quantidade += 1
            cp_obj.subtotal += cp_obj.avaliacao
            cp_obj.save()
            carro_obj.total += cp_obj.avaliacao
            carro_obj.save()
        elif acao == "dcr":
            cp_obj.quantidade -= 1
            cp_obj.subtotal -= cp_obj.avaliacao
            cp_obj.save()
            carro_obj.total -= cp_obj.avaliacao
            carro_obj.save()
            if cp_obj.quantidade == 0:
                cp_obj.delete()
        elif acao == "rmv":
            carro_obj.total -= cp_obj.subtotal
            carro_obj.save()
            cp_obj.delete()

        return redirect("lojaapp:meucarro")


class LimparCarroView(LojaMixin, View):
    def get(self, request, *args, **kwargs):
        carro_id = request.session.get("carro_id", None)
        if carro_id:
            carro = Carro.objects.get(id=carro_id)
            carro.carroproduto_set.all().delete()
            carro.total = 0
            carro.save()
        return redirect("lojaapp:meucarro")


class CheckoutView(LojaMixin, CreateView):
    template_name = "processar.html"
    form_class = Checar_PedidoForm
    success_url = reverse_lazy("lojaapp:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.cliente:
            pass
        else:
            return redirect("/entrar/?next=/checkout/")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carro_id = self.request.session.get("carro_id", None)
        if carro_id:
            carro_obj = Carro.objects.get(id=carro_id)
        else:
            carro_obj = None
        context["carro"] = carro_obj
        return context
    
    def form_valid(self, form):
        carro_id = self.request.session.get("carro_id")
        if carro_id:
            carro_obj = Carro.objects.get(id=carro_id)
            form.instance.carro = carro_obj
            form.instance.subtotal = carro_obj.total
            form.instance.desconto = 0
            form.instance.total = carro_obj.total
            form.instance.pedido_status = "Pedido Recebido"
            del self.request.session['carro_id']
            pm = form.cleaned_data.get("pagamento_method")
            pedido = form.save()
            if pm == "Khalti":
                return redirect(reverse("lojaapp:pagamento") + "?o_id=" + str(Pedido_order.id))
        else:
            return redirect("lojaapp:home")
        return super().form_valid(form)


class PagamentoView(View):
    def get(self, request, *args, **kwargs):
        o_id = request.GET.get("o_id")

        if not o_id or not o_id.isdigit():
            return redirect("lojaapp:home")  

        try:
            pedido = Pedido_order.objects.get(id=int(o_id))
            context = {
                "pedido": pedido
            }
        except Pedido_order.DoesNotExist:
            return redirect("lojaapp:home")
        
        return render(request, "pagamento.html", context)

 



class MeuCarroView(LojaMixin, TemplateView):
    template_name = "meucarro.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carro_id = self.request.session.get("carro_id", None)
        if carro_id:
            carro = Carro.objects.get(id=carro_id)
        else:
            carro = None
        context['carro'] = carro
        return context


class ClienteRegistrarView(CreateView):
    template_name = "clienteregistrar.html"
    form_class = ClienteRegistrarForm
    success_url = reverse_lazy("lojaapp:home")

    def form_valid(self, form):
        username = form.cleaned_data.get("username")
        email = form.cleaned_data.get("email")
        password = form.cleaned_data.get("senha") 

        if not username or not email or not password:
            form.add_error(None, "Todos os campos são obrigatórios.")
            return self.form_invalid(form)

        user = User.objects.create_user(username=username, email=email, password=password)
        form.instance.user = user

        login(self.request, user)
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.GET.get("next")
        return next_url if next_url else self.success_url



class ClienteEntrarView(FormView):
    template_name = "clienteentrar.html"
    form_class = ClienteEntrarForm
    success_url = reverse_lazy("lojaapp:home")

    def form_valid(self, form):
        unome = form.cleaned_data.get("username")
        pword = form.cleaned_data.get("password")
        usr = authenticate(username=unome, password=pword)
        if usr is not None and Cliente.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {
                "form": self.form_class,
                "error": "Usuário e senha não correspondem ."
            })
        return super().form_valid(form)


    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url


class ClienteSairView(LojaMixin, View):
    def get(self, request):
        logout(request)
        return redirect("lojaapp:home")


class SobreView(LojaMixin, TemplateView):
    template_name = "sobre.html"


class ContatoView(LojaMixin, TemplateView):
    template_name = "contato.html"


class ClientePerfilView(TemplateView):
    template_name = "clienteperfil.html"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Cliente.objects.filter(user=request.user).exists():
            pass
        else:
            return redirect("/entrar/?next=/perfil/")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cliente = self.request.user.cliente
        context['cliente'] = cliente

        Pedidos = Pedido_order.objects.filter(carro__cliente=cliente).order_by("-id")
        context['pedidos'] = Pedidos
        return context
    

class ClientePedidoDetalheView(DetailView):
    template_name = "clientepedidodetalhe.html"
    model = Pedido_order
    context_object_name = "pedido_obj"
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and Cliente.objects.filter(user=request.user).exists():
            order_id = self.kwargs["pk"]
            pedido=Pedido_order.objects.get(id=order_id)
            if request.user.cliente != pedido.carro.cliente:
                return redirect("lojaapp:clienteperfil")
        else:
            return redirect("/entrar/?next=/perfil/")
        return super().dispatch(request, *args, **kwargs)


class AdminLoginView(FormView):
    template_name = "admin_paginas/adminlogin.html"
    form_class = ClienteEntrarForm
    success_url = reverse_lazy("lojaapp:adminhome")

    def form_valid(self, form):
        unome = form.cleaned_data.get("username")
        pword = form.cleaned_data.get("password")
        usr = authenticate(username=unome, password=pword)
        if usr is not None and Admin.objects.filter(user=usr).exists():
            login(self.request, usr)
        else:
            return render(self.request, self.template_name, {
                "form": self.form_class,
                "error": "Usuário e senha não correspondem ."
            })
        return super().form_valid(form)


    def get_success_url(self):
        if "next" in self.request.GET:
            next_url = self.request.GET.get("next")
            return next_url
        else:
            return self.success_url

class AdminRequireMixin(object):

    def dispatch(self,request, *args, **kwargs):
        if request.user.is_autheticated and Admin.objects.filter(user=request.user).exists():
          pass
        else:
            return redirect("/admin-login/")
        return super().dispatch(request, *args, **kwargs)


class AdminHomeView(AdminRequireMixin, TemplateView):
    template_name = "admin_paginas/adminhome.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["PedidosPendentes"] = Pedido_order.objects.filter(pedido_status="Pedido Recebido").order_by("-id")
        return context
    
       

    
class AdminPedidoDetalheView(AdminRequireMixin, DetailView):
    template_name = "admin_paginas/adminpedidodetalhe.html"

    model = Pedido_order

    context_object_name = "pedido_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["todosstatus"] = PEDIDO_STATUS

        return context


class AdminPedidoListaView(AdminRequireMixin, ListView):
    template_name = "admin_paginas/adminpedidolista.html"

    queryset = Pedido_order.objects.all().order_by("-id")
    context_object_name = "todospedido"


class AdminPedidoMudarStatusView(AdminRequireMixin, View):
    def post (self,request, *args, **kwargs):
        pedido_id = self.kwargs["pk"]
        pedido_obj = Pedido_order.objects.get(id=pedido_id)
        novo_status = request.POST.get("status")
        pedido_obj.pedido_status = novo_status
        pedido_obj.save()

        return redirect(reverse_lazy("lojaapp:adminpedidodetalhe", kwargs={"pk" : self.kwargs["pk"]}))
    

class PesquisarView(TemplateView):
    template_name = "pesquisar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        kw = self.request.GET.get("keyword")
        results = Produto.objects.filter(
            Q(titulo__icontains=kw) | Q(descricao__icontains=kw) | Q(return_devolucao__icontains=kw))
        context["results"] = results

        return context

