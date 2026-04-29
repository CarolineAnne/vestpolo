from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Produto


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

    carrinho[id] = carrinho.get(id, 0) + 1

    request.session['carrinho'] = carrinho

    return redirect('home')


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