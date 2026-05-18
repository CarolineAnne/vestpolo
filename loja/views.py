from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Produto
from urllib.parse import quote
from .models import Produto, Pedido, ItemPedido

def home(request):
    produtos = Produto.objects.all()

    busca = request.GET.get('busca')
    tamanho = request.GET.get('tamanho')

    # 🔎 Busca
    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca) |
            Q(descricao__icontains=busca)
        )

    # 🎯 Filtro
    if tamanho:
        produtos = produtos.filter(tamanho=tamanho)

    # ❤️ Favoritos
    favoritos = request.session.get('favoritos', [])
    favoritos = [int(f) for f in favoritos]
    total_favoritos = len(favoritos)

    # 🛒 Carrinho
    carrinho = request.session.get('carrinho', {})
    total_itens = sum(carrinho.values())

    return render(request, 'loja/home.html', {
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
    favoritos = request.session.get('favoritos', [])
    favoritos = [int(f) for f in favoritos]

    if id in favoritos:
        favoritos.remove(id)
    else:
        favoritos.append(id)

    request.session['favoritos'] = favoritos

    return redirect('home')


def favoritos(request):
    favoritos_ids = request.session.get('favoritos', [])
    favoritos_ids = [int(f) for f in favoritos_ids]

    produtos = Produto.objects.filter(id__in=favoritos_ids)

    carrinho = request.session.get('carrinho', {})
    total_itens = sum(carrinho.values())

    return render(request, 'loja/favoritos.html', {
        'produtos': produtos,
        'total_itens': total_itens,
        'total_favoritos': len(favoritos_ids)
    })


def adicionar_carrinho(request, id):

    carrinho = request.session.get('carrinho', {})

    id = str(id)

    quantidade = int(request.GET.get('quantidade', 1))

    if quantidade < 1:
        quantidade = 1

    if id in carrinho:
        carrinho[id] += quantidade
    else:
        carrinho[id] = quantidade

    request.session['carrinho'] = carrinho

    return redirect('carrinho')


def remover_carrinho(request, id):
    carrinho = request.session.get('carrinho', {})
    id = str(id)

    if id in carrinho:
        del carrinho[id]

    request.session['carrinho'] = carrinho

    return redirect('carrinho')


def carrinho(request):
    carrinho = request.session.get('carrinho', {})

    itens = []
    total = 0

    for id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=id)
        subtotal = produto.preco * quantidade

        itens.append({
            'produto': produto,
            'quantidade': quantidade,
            'subtotal': subtotal
        })

        total += subtotal

    favoritos = request.session.get('favoritos', [])

    return render(request, 'loja/carrinho.html', {
        'itens': itens,
        'total': total,
        'total_itens': sum(carrinho.values()),
        'total_favoritos': len(favoritos)
    })


def aumentar_quantidade(request, id):
    carrinho = request.session.get('carrinho', {})
    id = str(id)

    if id in carrinho:
        carrinho[id] += 1

    request.session['carrinho'] = carrinho

    return redirect('carrinho')


def diminuir_quantidade(request, id):
    carrinho = request.session.get('carrinho', {})
    id = str(id)

    if id in carrinho:
        carrinho[id] -= 1

        if carrinho[id] <= 0:
            del carrinho[id]

    request.session['carrinho'] = carrinho

    return redirect('carrinho')

def finalizar_whatsapp(request):
    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        return redirect('carrinho')

    pedido = Pedido.objects.create(total=0)

    mensagem = "Olá! Tenho interesse em finalizar este pedido:\n\n"
    total = 0

    for id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=id)
        subtotal = produto.preco * quantidade
        total += subtotal

        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=quantidade,
            subtotal=subtotal
        )

        mensagem += f"- {produto.nome}\n"
        mensagem += f"  Tamanho: {produto.tamanho}\n"
        mensagem += f"  Quantidade: {quantidade}\n"
        mensagem += f"  Subtotal: R$ {subtotal:.2f}\n\n"

    pedido.total = total
    pedido.save()

    mensagem += f"Total do pedido: R$ {total:.2f}\n"
    mensagem += f"Número do pedido: #{pedido.id}\n\n"
    mensagem += "Aguardo o atendimento."

    request.session['carrinho'] = {}

    texto = quote(mensagem)
    numero_whatsapp = "5574999087655"

    url = f"https://wa.me/{numero_whatsapp}?text={texto}"

    return redirect(url)