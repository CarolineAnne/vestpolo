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
    return redirect('checkout')

def checkout(request):
    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        return redirect('carrinho')

    produtos = []
    total = 0

    for id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=id)
        subtotal = produto.preco * quantidade
        total += subtotal

        produtos.append({
            'produto': produto,
            'quantidade': quantidade,
            'subtotal': subtotal
        })

    if request.method == 'POST':
        nome_cliente = request.POST.get('nome_cliente')
        telefone = request.POST.get('telefone')
        forma_entrega = request.POST.get('forma_entrega')
        observacao = request.POST.get('observacao')

        pedido = Pedido.objects.create(
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
                subtotal=item['subtotal']
            )

            mensagem += f"- {item['produto'].nome}\n"
            mensagem += f"  Tamanho: {item['produto'].tamanho}\n"
            mensagem += f"  Quantidade: {item['quantidade']}\n"
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