from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from urllib.parse import quote
from decimal import Decimal
from .models import Produto, Pedido, ItemPedido, Favorito
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


FORMAS_ENTREGA = ("Retirada", "Entrega", "Combinar pelo WhatsApp")

FORMAS_PAGAMENTO = (
    "Pix",
    "Cartao de credito",
    "Cartao de debito",
    "Boleto",
    "Dinheiro na retirada",
    "Combinar pelo WhatsApp",
)


def apenas_digitos(valor):
    return ''.join(caractere for caractere in valor if caractere.isdigit())


def formatar_cep(cep):
    digitos = apenas_digitos(cep)
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return cep


def formatar_moeda(valor):
    return f"{valor:.2f}".replace('.', ',')


def calcular_frete(cep, quantidade_total, forma_entrega):
    quantidade_total = max(int(quantidade_total or 1), 1)

    if forma_entrega == "Retirada":
        return {
            "valor": Decimal("0.00"),
            "transportadora": "VestPolo",
            "servico": "Retirada",
            "prazo": 0,
            "descricao": "Retirada sem frete",
        }

    if forma_entrega == "Combinar pelo WhatsApp":
        return {
            "valor": Decimal("0.00"),
            "transportadora": "A combinar",
            "servico": "A combinar pelo WhatsApp",
            "prazo": None,
            "descricao": "Frete a combinar",
        }

    digitos = apenas_digitos(cep)
    if len(digitos) != 8:
        return None

    prefixo = int(digitos[0])

    if digitos.startswith(("489", "563")):
        return {
            "valor": Decimal("0.00"),
            "transportadora": "VestPolo",
            "servico": "Entrega local gratuita",
            "prazo": 2,
            "descricao": "Entrega gratis para Petrolina e Juazeiro - ate 2 dias uteis",
        }

    if prefixo in (4, 5):
        base = Decimal("32.90")
        extra = Decimal("3.50")
        prazo = 7
        servico = "PAC estimado - Nordeste"
    elif prefixo in (0, 1, 2, 3):
        base = Decimal("39.90")
        extra = Decimal("4.50")
        prazo = 9
        servico = "PAC estimado - Sudeste"
    elif prefixo == 7:
        base = Decimal("42.90")
        extra = Decimal("4.90")
        prazo = 10
        servico = "PAC estimado - Centro-Oeste"
    elif prefixo in (8, 9):
        base = Decimal("44.90")
        extra = Decimal("5.50")
        prazo = 11
        servico = "PAC estimado - Sul"
    else:
        base = Decimal("46.90")
        extra = Decimal("5.90")
        prazo = 12
        servico = "PAC estimado - Norte"

    valor = base + (extra * Decimal(quantidade_total - 1))

    return {
        "valor": valor,
        "transportadora": "Transportadora parceira",
        "servico": servico,
        "prazo": prazo,
        "descricao": f"{servico} - ate {prazo} dias uteis",
    }

def home(request):
    produtos = Produto.objects.all()

    busca = request.GET.get('busca')

    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca) |
            Q(descricao__icontains=busca)
        )

    produtos_universitarios = Produto.objects.filter(categoria='Universitário')
    produtos_empresariais = Produto.objects.filter(categoria='Empresarial')
    produtos_personalizados = Produto.objects.filter(categoria='Personalizado')

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

    return render(request, 'loja/home.html', {
        'produtos': produtos,
        'produtos_universitarios': produtos_universitarios,
        'produtos_empresariais': produtos_empresariais,
        'produtos_personalizados': produtos_personalizados,
        'favoritos': favoritos,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos
    })

def personalizados(request):
    produtos = Produto.objects.filter(categoria='Personalizado')

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

def universitarios(request):
    produtos = Produto.objects.filter(categoria='Universitário')

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

    return render(request, 'loja/categoria.html', {
        'produtos': produtos,
        'favoritos': favoritos,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos,
        'titulo': 'Universitários',
        'subtitulo': 'Polos universitárias personalizadas',
        'descricao_pagina': 'Polos bordadas para cursos, turmas, eventos acadêmicos e formandos.',
        'badge': 'Universitário',
        'icone': '🎓',
        'banner_imagem': 'img/universitarios-destaque.png',
    })


def empresariais(request):
    produtos = Produto.objects.filter(categoria='Empresarial')

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

    return render(request, 'loja/categoria.html', {
        'produtos': produtos,
        'favoritos': favoritos,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos,
        'titulo': 'Empresariais',
        'subtitulo': 'Uniformes profissionais personalizados',
        'descricao_pagina': 'Polos bordadas para empresas, equipes, instituições e eventos corporativos.',
        'badge': 'Empresarial',
        'icone': '🏢',
        'banner_imagem': 'img/empresariais-destaque.png',
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
    subtotal_pedido = Decimal("0.00")
    total_itens = 0

    for chave, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=dados['produto_id'])
        quantidade = dados['quantidade']
        subtotal = produto.preco * quantidade
        subtotal_pedido += subtotal
        total_itens += quantidade

        produtos.append({
            'chave': chave,
            'produto': produto,
            'quantidade': quantidade,
            'tamanho': dados.get('tamanho', ''),
            'cor': dados.get('cor', ''),
            'subtotal': subtotal
        })
    if request.method == 'POST':
        nome_cliente = request.POST.get('nome_cliente', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        forma_entrega = request.POST.get('forma_entrega', '').strip()
        forma_pagamento = request.POST.get('forma_pagamento', '').strip()
        observacao = request.POST.get('observacao', '').strip()

        cep_entrega = request.POST.get('cep_entrega', '').strip()
        endereco = request.POST.get('endereco', '').strip()
        numero = request.POST.get('numero', '').strip()
        complemento = request.POST.get('complemento', '').strip()
        bairro = request.POST.get('bairro', '').strip()
        cidade = request.POST.get('cidade', '').strip()
        estado = request.POST.get('estado', '').strip().upper()[:2]

        curso = request.POST.get('curso', '')
        nome_bordado = request.POST.get('nome_bordado', '')
        observacao_item = request.POST.get('observacao_item', '')

        arte = request.FILES.get('arte')

        if forma_entrega not in FORMAS_ENTREGA:
            messages.error(request, 'Escolha uma forma de entrega valida.')
            return redirect('checkout')

        if forma_pagamento not in FORMAS_PAGAMENTO:
            messages.error(request, 'Escolha uma forma de pagamento valida.')
            return redirect('checkout')

        if forma_entrega == "Entrega":
            campos_entrega = [cep_entrega, endereco, numero, bairro, cidade, estado]
            if any(not campo for campo in campos_entrega):
                messages.error(request, 'Preencha o endereco completo para entrega.')
                return redirect('checkout')

        frete = calcular_frete(cep_entrega, total_itens, forma_entrega)

        if frete is None:
            messages.error(request, 'Informe um CEP valido com 8 numeros.')
            return redirect('checkout')

        total_final = subtotal_pedido + frete["valor"]

        pedido = Pedido.objects.create(
            usuario=request.user if request.user.is_authenticated else None,
            nome_cliente=nome_cliente,
            telefone=telefone,
            forma_entrega=forma_entrega,
            cep_entrega=formatar_cep(cep_entrega),
            endereco=endereco,
            numero=numero,
            complemento=complemento,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            observacao=observacao,
            subtotal=subtotal_pedido,
            valor_frete=frete["valor"],
            transportadora=frete["transportadora"],
            servico_frete=frete["servico"],
            prazo_entrega=frete["prazo"],
            total=total_final,
            forma_pagamento=forma_pagamento,
        )

        mensagem = "Olá! Quero finalizar este pedido:\n\n"

        mensagem += f"Pedido #{pedido.id}\n"
        mensagem += f"Cliente: {nome_cliente}\n"
        mensagem += f"Telefone: {telefone}\n"
        mensagem += f"Entrega/Retirada: {forma_entrega}\n"
        mensagem += f"Forma de pagamento: {forma_pagamento}\n"

        if forma_entrega == "Entrega":
            mensagem += "\nEndereco de entrega:\n"
            mensagem += f"CEP: {formatar_cep(cep_entrega)}\n"
            mensagem += f"Endereco: {endereco}, {numero}\n"
            if complemento:
                mensagem += f"Complemento: {complemento}\n"
            mensagem += f"Bairro: {bairro}\n"
            mensagem += f"Cidade/UF: {cidade}/{estado}\n"

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

        mensagem += f"Subtotal dos produtos: R$ {formatar_moeda(subtotal_pedido)}\n"
        mensagem += f"Frete: R$ {formatar_moeda(frete['valor'])} ({frete['descricao']})\n"
        mensagem += f"Total: R$ {formatar_moeda(total_final)}\n\n"
        mensagem += "Aguardo o atendimento."

        request.session['carrinho'] = {}

        texto = quote(mensagem)
        numero_whatsapp = "5574999087655"

        return redirect(f"https://wa.me/{numero_whatsapp}?text={texto}")

    return render(request, 'loja/checkout.html', {
        'itens': produtos,
        'subtotal': subtotal_pedido,
        'total': subtotal_pedido,
        'total_itens': total_itens,
        'formas_pagamento': FORMAS_PAGAMENTO
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
