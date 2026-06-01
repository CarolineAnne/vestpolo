from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from urllib.parse import quote
from .models import Produto, Pedido, ItemPedido, Favorito
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def home(request):
    produtos = Produto.objects.all()

    busca = request.GET.get('busca')

    # 🔎 Busca
    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca) |
            Q(descricao__icontains=busca)
        )

    # ❤️ Favoritos
    if request.user.is_authenticated:
        favoritos = list(
            Favorito.objects.filter(usuario=request.user)
            .values_list('produto_id', flat=True)
        )
    else:
        favoritos = []

    total_favoritos = len(favoritos)

    # 🛒 Carrinho
    carrinho = request.session.get('carrinho', {})

    total_itens = 0

    for item in carrinho.values():
        if isinstance(item, dict):
            total_itens += item.get('quantidade', 0)
        else:
            total_itens += item

    return render(request, 'loja/home.html', {
        'produtos': produtos,
        'favoritos': favoritos,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos
    })

def personalizados(request):
    produtos = Produto.objects.filter(
        Q(categoria__icontains='personalizado') |
        Q(categoria__icontains='personalizados') |
        Q(nome__icontains='personalizado') |
        Q(nome__icontains='personalizados')
    )

    if request.user.is_authenticated:
        favoritos = list(
            Favorito.objects.filter(usuario=request.user)
            .values_list('produto_id', flat=True)
        )
    else:
        favoritos = []

    total_favoritos = len(favoritos)

    carrinho = request.session.get('carrinho', {})

    total_itens = 0

    for item in carrinho.values():
        if isinstance(item, dict):
            total_itens += item.get('quantidade', 0)
        else:
            total_itens += item

    return render(request, 'loja/personalizados.html', {
        'produtos': produtos,
        'favoritos': favoritos,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos
    })

def produto_detalhe(request, id):
    produto = get_object_or_404(Produto, id=id)

    return render(request, 'loja/produto.html', {
        'produto': produto
    })


def favoritar(request, id):
    if not request.user.is_authenticated:
        return redirect('login')

    produto = get_object_or_404(Produto, id=id)

    favorito, criado = Favorito.objects.get_or_create(
        usuario=request.user,
        produto=produto
    )

    if not criado:
        favorito.delete()

    return redirect(request.META.get('HTTP_REFERER', 'home'))


def favoritos(request):
    if not request.user.is_authenticated:
        return redirect('login')

    favoritos_usuario = Favorito.objects.filter(
        usuario=request.user
    ).select_related('produto')

    produtos = [fav.produto for fav in favoritos_usuario]

    return render(request, 'loja/favoritos.html', {
        'produtos': produtos
    })

def adicionar_carrinho(request, id):

    carrinho = request.session.get('carrinho', {})

    produto = get_object_or_404(Produto, id=id)

    try:
        quantidade = int(request.GET.get('quantidade', 1))
    except ValueError:
        quantidade = 1

    if quantidade < 1:
        quantidade = 1

    tamanho = request.GET.get('tamanho', '')
    cor = request.GET.get('cor', '')

    if not tamanho or not cor:
        return redirect('produto_detalhe', id=id)

    chave = f"{id}_{tamanho}_{cor}"

    if chave in carrinho:
        carrinho[chave]['quantidade'] += quantidade
    else:
        carrinho[chave] = {
            'produto_id': produto.id,
            'quantidade': quantidade,
            'tamanho': tamanho,
            'cor': cor
        }

    request.session['carrinho'] = carrinho

    return redirect('carrinho')


def remover_carrinho(request, chave):
    carrinho = request.session.get('carrinho', {})

    if chave in carrinho:
        del carrinho[chave]

    request.session['carrinho'] = carrinho
    request.session.modified = True

    return redirect('carrinho')

def carrinho(request):
    carrinho = request.session.get('carrinho', {})

    itens = []
    total = 0
    total_itens = 0

    for chave, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=dados['produto_id'])
        quantidade = dados['quantidade']
        subtotal = produto.preco * quantidade

        itens.append({
            'chave': chave,
            'produto': produto,
            'quantidade': quantidade,
            'tamanho': dados.get('tamanho', ''),
            'cor': dados.get('cor', ''),
            'subtotal': subtotal
        })

        total += subtotal
        total_itens += quantidade

    if request.user.is_authenticated:
        total_favoritos = Favorito.objects.filter(usuario=request.user).count()
    else:
        total_favoritos = 0

    return render(request, 'loja/carrinho.html', {
        'itens': itens,
        'total': total,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos
    })

def aumentar_quantidade(request, chave):
    carrinho = request.session.get('carrinho', {})

    if chave in carrinho:
        carrinho[chave]['quantidade'] += 1

    request.session['carrinho'] = carrinho
    request.session.modified = True

    return redirect('carrinho')


def diminuir_quantidade(request, chave):
    carrinho = request.session.get('carrinho', {})

    if chave in carrinho:
        carrinho[chave]['quantidade'] -= 1

        if carrinho[chave]['quantidade'] <= 0:
            del carrinho[chave]

    request.session['carrinho'] = carrinho
    request.session.modified = True

    return redirect('carrinho')

def finalizar_whatsapp(request):
    return redirect('checkout')

def checkout(request):
    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        return redirect('carrinho')

    produtos = []
    total = 0

    for chave, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=dados['produto_id'])
        quantidade = dados['quantidade']
        subtotal = produto.preco * quantidade
        total += subtotal

        produtos.append({
            'chave': chave,
            'produto': produto,
            'quantidade': quantidade,
            'tamanho': dados.get('tamanho', ''),
            'cor': dados.get('cor', ''),
            'subtotal': subtotal
        })
    if request.method == 'POST':
        nome_cliente = request.POST.get('nome_cliente')
        telefone = request.POST.get('telefone')
        forma_entrega = request.POST.get('forma_entrega')
        observacao = request.POST.get('observacao')

        curso = request.POST.get('curso', '')
        nome_bordado = request.POST.get('nome_bordado', '')
        observacao_item = request.POST.get('observacao_item', '')

        arte = request.FILES.get('arte')

        pedido = Pedido.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            nome_cliente=nome_cliente,
            telefone=telefone,
            forma_entrega=forma_entrega,
            observacao=observacao,
            total=total
        )

        mensagem = "Olá! Quero finalizar este pedido:\n\n"

        mensagem += f"Pedido #{pedido.id}\n"
        mensagem += f"Cliente: {nome_cliente}\n"
        mensagem += f"Telefone: {telefone}\n"
        mensagem += f"Entrega/Retirada: {forma_entrega}\n"

        if observacao:
            mensagem += f"Observação: {observacao}\n"

        mensagem += "\nItens:\n"

        for item in produtos:

            ItemPedido.objects.create(
                pedido=pedido,
                produto=item['produto'],
                quantidade=item['quantidade'],
                tamanho=item['tamanho'],
                cor=item['cor'],
                curso=curso,
                nome_bordado=nome_bordado,
                observacao=observacao_item,
                arte=arte,
                subtotal=item['subtotal']
            )

            mensagem += f"- {item['produto'].nome}\n"
            mensagem += f"  Tamanho: {item['tamanho']}\n"
            mensagem += f"  Cor: {item['cor']}\n"
            mensagem += f"  Quantidade: {item['quantidade']}\n"

            if curso:
                mensagem += f"  Curso/Turma/Empresa: {curso}\n"

            if nome_bordado:
                mensagem += f"  Nome bordado: {nome_bordado}\n"

            if observacao_item:
                mensagem += f"  Detalhes do bordado: {observacao_item}\n"

            if arte:
                mensagem += "  Arte/logo enviada no pedido.\n"

            mensagem += f"  Subtotal: R$ {item['subtotal']:.2f}\n\n"

        mensagem += f"Total: R$ {total:.2f}\n\n"
        mensagem += "Aguardo o atendimento."

        request.session['carrinho'] = {}

        texto = quote(mensagem)
        numero_whatsapp = "5574999087655"

        return redirect(f"https://wa.me/{numero_whatsapp}?text={texto}")

    return render(request, 'loja/checkout.html', {
        'itens': produtos,
        'total': total
    })

def cadastro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        if User.objects.filter(username=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado.')
            return redirect('cadastro')

        usuario = User.objects.create_user(
            username=email,
            email=email,
            first_name=nome,
            password=senha
        )

        login(request, usuario)
        return redirect('minha_conta')

    return render(request, 'loja/cadastro.html')


def login_usuario(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        usuario = authenticate(request, username=email, password=senha)

        if usuario is not None:
            login(request, usuario)
            return redirect('minha_conta')
        else:
            messages.error(request, 'E-mail ou senha inválidos.')

    return render(request, 'loja/login.html')


def logout_usuario(request):
    logout(request)
    return redirect('home')


def minha_conta(request):
    if not request.user.is_authenticated:
        return redirect('login')

    return render(request, 'loja/minha_conta.html')

def meus_pedidos(request):
    if not request.user.is_authenticated:
        return redirect('login')

    pedidos = Pedido.objects.filter(usuario=request.user).order_by('-data_pedido')

    return render(request, 'loja/meus_pedidos.html', {
        'pedidos': pedidos
    })