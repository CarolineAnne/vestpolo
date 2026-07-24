import json
import re
import unicodedata

import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Prefetch
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from urllib.parse import quote
from decimal import Decimal
from .models import (
    Produto,
    ProdutoFoto,
    Pedido,
    ItemPedido,
    Favorito,
    AdicionalPersonalizacao,
    OrcamentoPersonalizado,
)
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

PAGAMENTOS_ONLINE = (
    "Pix",
    "Cartao de credito",
    "Cartao de debito",
    "Boleto",
)

OBSERVACAO_PRAZO_ENTREGA = (
    "Prazo estimado sujeito a disponibilidade em estoque. "
    "Caso demore mais que o estimado, a VestPolo informara o cliente."
)

NUMERO_WHATSAPP_ATENDIMENTO = "5574999087655"


def produtos_com_fotos(queryset):
    return queryset.prefetch_related(
        Prefetch(
            'fotos',
            queryset=ProdutoFoto.objects.filter(ativo=True).order_by('ordem', 'id'),
            to_attr='fotos_ativas'
        )
    )


def apenas_digitos(valor):
    return ''.join(caractere for caractere in valor if caractere.isdigit())


def formatar_cep(cep):
    digitos = apenas_digitos(cep)
    if len(digitos) == 8:
        return f"{digitos[:5]}-{digitos[5:]}"
    return cep


def formatar_telefone(telefone):
    digitos = apenas_digitos(telefone)

    if len(digitos) > 11 and digitos.startswith("55"):
        digitos = digitos[2:]

    if len(digitos) == 11:
        return f"({digitos[:2]}) {digitos[2:7]}-{digitos[7:]}"

    if len(digitos) == 10:
        return f"({digitos[:2]}) {digitos[2:6]}-{digitos[6:]}"

    return telefone


def formatar_documento(documento):
    digitos = apenas_digitos(documento)

    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"

    if len(digitos) == 14:
        return (
            f"{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/"
            f"{digitos[8:12]}-{digitos[12:]}"
        )

    return documento


def formatar_moeda(valor):
    return f"{valor:.2f}".replace('.', ',')


def decimal_request(valor):
    try:
        return Decimal(str(valor or "0").strip().replace(",", "."))
    except Exception:
        return Decimal("0.00")


def normalizar_texto_pagamento(valor, limite):
    texto = unicodedata.normalize("NFKD", valor or "")
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^A-Z0-9 $%*+\-./:]", "", texto.upper())
    texto = re.sub(r"\s+", " ", texto).strip()
    return (texto or "VESTPOLO")[:limite]


def campo_pix(identificador, valor):
    return f"{identificador}{len(valor):02d}{valor}"


def crc16_pix(payload):
    resultado = 0xFFFF

    for caractere in payload:
        resultado ^= ord(caractere) << 8
        for _ in range(8):
            if resultado & 0x8000:
                resultado = (resultado << 1) ^ 0x1021
            else:
                resultado <<= 1
            resultado &= 0xFFFF

    return f"{resultado:04X}"


def gerar_codigo_pix(pedido):
    chave_pix = settings.PIX_CHAVE.strip()

    if not chave_pix:
        return ""

    nome_recebedor = normalizar_texto_pagamento(settings.PIX_NOME_RECEBEDOR, 25)
    cidade_recebedor = normalizar_texto_pagamento(settings.PIX_CIDADE_RECEBEDOR, 15)
    txid = normalizar_texto_pagamento(f"VP{pedido.id}", 25)
    valor = f"{pedido.total:.2f}"

    conta_recebedor = (
        campo_pix("00", "br.gov.bcb.pix")
        + campo_pix("01", chave_pix)
        + campo_pix("02", f"Pedido {pedido.id}")
    )

    dados_adicionais = campo_pix("05", txid)

    payload = (
        campo_pix("00", "01")
        + campo_pix("26", conta_recebedor)
        + campo_pix("52", "0000")
        + campo_pix("53", "986")
        + campo_pix("54", valor)
        + campo_pix("58", "BR")
        + campo_pix("59", nome_recebedor)
        + campo_pix("60", cidade_recebedor)
        + campo_pix("62", dados_adicionais)
    )

    payload_com_crc = payload + "6304"
    return payload_com_crc + crc16_pix(payload_com_crc)


def criar_preferencia_mercado_pago(pedido, request):
    token = settings.MERCADO_PAGO_ACCESS_TOKEN.strip()

    if not token:
        return ""

    url_retorno = request.build_absolute_uri(
        reverse("pagamento_pedido", args=[pedido.id])
    )
    url_webhook = request.build_absolute_uri(reverse("mercado_pago_webhook"))

    payload = {
        "items": [
            {
                "title": f"Pedido #{pedido.id} VestPolo",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(pedido.total),
            }
        ],
        "payer": {
            "name": pedido.nome_cliente,
        },
        "external_reference": str(pedido.id),
        "statement_descriptor": "VESTPOLO",
        "back_urls": {
            "success": f"{url_retorno}?status=aprovado",
            "pending": f"{url_retorno}?status=pendente",
            "failure": f"{url_retorno}?status=recusado",
        },
        "notification_url": url_webhook,
        "auto_return": "approved",
        "metadata": {
            "pedido_id": pedido.id,
            "forma_pagamento": pedido.forma_pagamento,
        },
    }

    try:
        resposta = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
            timeout=12,
        )
        resposta.raise_for_status()
    except requests.RequestException:
        return ""

    dados = resposta.json()
    preferencia_id = dados.get("id", "")

    if preferencia_id:
        pedido.mercado_pago_id = preferencia_id[:100]
        pedido.save(update_fields=["mercado_pago_id"])

    return dados.get("init_point") or dados.get("sandbox_init_point") or ""


def montar_mensagem_pedido(pedido):
    mensagem = "Olá! Quero finalizar este pedido:\n\n"
    mensagem += f"Pedido #{pedido.id}\n"
    mensagem += f"Cliente: {pedido.nome_cliente}\n"
    mensagem += f"Telefone: {pedido.telefone}\n"
    mensagem += f"Entrega/Retirada: {pedido.forma_entrega}\n"
    mensagem += f"Forma de pagamento: {pedido.forma_pagamento}\n"

    if pedido.forma_entrega == "Entrega":
        mensagem += "\nEndereco de entrega:\n"
        mensagem += f"CEP: {pedido.cep_entrega}\n"
        mensagem += f"Endereco: {pedido.endereco}, {pedido.numero}\n"
        if pedido.complemento:
            mensagem += f"Complemento: {pedido.complemento}\n"
        mensagem += f"Bairro: {pedido.bairro}\n"
        mensagem += f"Cidade/UF: {pedido.cidade}/{pedido.estado}\n"

    if pedido.observacao:
        mensagem += f"Observação: {pedido.observacao}\n"

    mensagem += "\nItens:\n"

    for item in pedido.itens.select_related("produto").all():
        mensagem += f"- {item.produto.nome}\n"
        mensagem += f"  Tamanho: {item.tamanho}\n"
        mensagem += f"  Cor: {item.cor}\n"
        if item.modelagem:
            mensagem += f"  Modelagem: {item.modelagem}\n"
        mensagem += f"  Quantidade: {item.quantidade}\n"

        if item.curso:
            mensagem += f"  Curso/Turma/Empresa: {item.curso}\n"

        if item.nome_bordado:
            mensagem += f"  Nome bordado: {item.nome_bordado}\n"

        if item.observacao:
            mensagem += f"  Detalhes do bordado: {item.observacao}\n"

        if item.arte:
            mensagem += "  Arte/logo enviada no pedido.\n"

        mensagem += f"  Subtotal: R$ {formatar_moeda(item.subtotal)}\n\n"

    mensagem += f"Subtotal dos produtos: R$ {formatar_moeda(pedido.subtotal)}\n"
    mensagem += f"Frete: R$ {formatar_moeda(pedido.valor_frete)}"

    if pedido.servico_frete:
        mensagem += f" ({pedido.servico_frete})"

    mensagem += "\n"
    if pedido.forma_entrega == "Entrega":
        mensagem += f"Prazo: {OBSERVACAO_PRAZO_ENTREGA}\n"
    mensagem += f"Total: R$ {formatar_moeda(pedido.total)}\n\n"
    mensagem += "Aguardo o atendimento."

    return mensagem


def montar_link_whatsapp_pedido(pedido):
    texto = quote(montar_mensagem_pedido(pedido))
    return f"https://wa.me/{NUMERO_WHATSAPP_ATENDIMENTO}?text={texto}"


def status_pagamento_mercado_pago(status):
    mapa = {
        "approved": "Aprovado",
        "rejected": "Recusado",
        "cancelled": "Cancelado",
        "refunded": "Reembolsado",
        "charged_back": "Reembolsado",
    }
    return mapa.get(status, "Pendente")


def atualizar_pedido_por_pagamento_mercado_pago(pagamento_id):
    token = settings.MERCADO_PAGO_ACCESS_TOKEN.strip()

    if not token or not pagamento_id:
        return None

    try:
        resposta = requests.get(
            f"https://api.mercadopago.com/v1/payments/{pagamento_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=12,
        )
        resposta.raise_for_status()
    except requests.RequestException:
        return None

    pagamento = resposta.json()
    pedido_id = pagamento.get("external_reference")

    if not pedido_id:
        pedido_id = (pagamento.get("metadata") or {}).get("pedido_id")

    try:
        pedido = Pedido.objects.get(id=pedido_id)
    except (Pedido.DoesNotExist, TypeError, ValueError):
        return None

    novo_status = status_pagamento_mercado_pago(pagamento.get("status"))
    pedido.status_pagamento = novo_status
    pedido.mercado_pago_id = str(pagamento.get("id", ""))[:100]

    if novo_status == "Aprovado":
        pedido.status = "Em produção"

    pedido.save(update_fields=["status_pagamento", "mercado_pago_id", "status"])
    return pedido


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
            "descricao": (
                "Entrega gratis para Petrolina e Juazeiro - ate 2 dias uteis. "
                f"{OBSERVACAO_PRAZO_ENTREGA}"
            ),
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
        "descricao": (
            f"{servico} - ate {prazo} dias uteis. "
            f"{OBSERVACAO_PRAZO_ENTREGA}"
        ),
    }

def home(request):
    produtos = produtos_com_fotos(Produto.objects.exclude(categoria='Empresarial'))

    busca = request.GET.get('busca')

    if busca:
        produtos = produtos.filter(
            Q(nome__icontains=busca) |
            Q(descricao__icontains=busca)
        )

    produtos_universitarios = produtos_com_fotos(Produto.objects.filter(categoria='Universitário'))
    produtos_personalizados = produtos_com_fotos(Produto.objects.filter(categoria='Personalizado'))

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
        'produtos_personalizados': produtos_personalizados,
        'favoritos': favoritos,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos
    })

def personalizados(request):
    produtos = produtos_com_fotos(Produto.objects.filter(categoria='Personalizado'))
    adicionais_personalizacao = AdicionalPersonalizacao.objects.filter(ativo=True)

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
        'adicionais_personalizacao': adicionais_personalizacao,
        'favoritos': favoritos,
        'total_itens': total_itens,
        'total_favoritos': total_favoritos
    })


def orcamento_personalizado_whatsapp(request):
    if request.method != "POST":
        return JsonResponse({"erro": "metodo nao permitido"}, status=405)

    tipo_cliente = request.POST.get("tipo_cliente", "Pessoa").strip() or "Pessoa"
    nome_cliente = request.POST.get("nome_cliente", "").strip()
    documento = formatar_documento(request.POST.get("documento", "").strip())
    telefone = formatar_telefone(request.POST.get("telefone", "").strip())
    curso = request.POST.get("curso", "").strip()
    forma_entrega = request.POST.get("forma_entrega", "").strip()
    cep_entrega = request.POST.get("cep_entrega", "").strip()

    if not nome_cliente or not telefone:
        return JsonResponse(
            {"erro": "Preencha nome/empresa e WhatsApp para enviar o orcamento."},
            status=400
        )

    if forma_entrega not in FORMAS_ENTREGA:
        return JsonResponse(
            {"erro": "Escolha uma forma de entrega valida."},
            status=400
        )

    try:
        quantidade = max(int(request.POST.get("quantidade", 1) or 1), 1)
    except ValueError:
        quantidade = 1

    frete = calcular_frete(cep_entrega, quantidade, forma_entrega)

    if frete is None:
        return JsonResponse(
            {"erro": "Informe um CEP valido com 8 numeros para calcular o frete."},
            status=400
        )

    produto = None
    produto_nome = request.POST.get("produto_nome", "").strip() or "Polo personalizada"
    produto_id = request.POST.get("produto_id", "").strip()

    if produto_id:
        try:
            produto = Produto.objects.get(id=produto_id, categoria="Personalizado")
            produto_nome = produto.nome
        except (Produto.DoesNotExist, ValueError):
            produto = None

    adicionais = []
    try:
        adicionais_raw = json.loads(request.POST.get("adicionais", "[]"))
    except ValueError:
        adicionais_raw = []

    if isinstance(adicionais_raw, list):
        for adicional in adicionais_raw:
            if not isinstance(adicional, dict):
                continue

            nome = str(adicional.get("nome", "")).strip()
            preco = decimal_request(adicional.get("preco"))

            if nome:
                adicionais.append({
                    "nome": nome,
                    "preco": preco,
                })

    adicionais_texto = "\n".join(
        f"{adicional['nome']}: R$ {formatar_moeda(adicional['preco'])}"
        for adicional in adicionais
    )

    subtotal_unidade = decimal_request(request.POST.get("subtotal_unidade"))
    total_estimado = decimal_request(request.POST.get("total_estimado"))

    if total_estimado <= 0:
        total_estimado = subtotal_unidade * Decimal(quantidade)

    total_final = total_estimado + frete["valor"]

    orcamento = OrcamentoPersonalizado.objects.create(
        produto=produto,
        tipo_cliente=tipo_cliente[:20],
        nome_cliente=nome_cliente,
        documento=documento,
        telefone=telefone,
        curso=curso,
        tamanho=request.POST.get("tamanho", "").strip(),
        modelagem=request.POST.get("modelagem", "").strip(),
        cor=request.POST.get("cor", "").strip(),
        quantidade=quantidade,
        adicionais=adicionais_texto,
        subtotal_unidade=subtotal_unidade,
        valor_frete=frete["valor"],
        total_estimado=total_final,
        forma_entrega=forma_entrega,
        cep_entrega=formatar_cep(cep_entrega) if cep_entrega else "",
        frete_descricao=frete["descricao"],
        arte=request.FILES.get("arte"),
        observacao=request.POST.get("observacao", "").strip(),
    )

    mensagem = "Ola! Quero um orcamento de polo personalizada.\n\n"
    mensagem += f"Orcamento #{orcamento.id}\n\n"
    mensagem += "Dados do cliente:\n"
    mensagem += f"Tipo: {orcamento.tipo_cliente}\n"
    mensagem += f"Nome/empresa: {orcamento.nome_cliente}\n"
    if orcamento.documento:
        mensagem += f"CPF/CNPJ: {orcamento.documento}\n"
    mensagem += f"WhatsApp: {orcamento.telefone}\n"
    if orcamento.curso:
        mensagem += f"Curso/turma/setor: {orcamento.curso}\n"

    mensagem += "\nPolo personalizada:\n"
    mensagem += f"Base: {produto_nome}\n"
    mensagem += f"Tamanho: {orcamento.tamanho or 'Nao informado'}\n"
    mensagem += f"Modelagem: {orcamento.modelagem or 'Nao informada'}\n"
    mensagem += f"Cor desejada: {orcamento.cor or 'A definir'}\n"
    mensagem += f"Quantidade: {orcamento.quantidade}\n"
    mensagem += "\nBordados escolhidos:\n"
    mensagem += adicionais_texto or "Sem bordados extras"
    mensagem += "\n\nValores:\n"
    mensagem += f"Subtotal por unidade: R$ {formatar_moeda(orcamento.subtotal_unidade)}\n"
    mensagem += f"Produtos e bordados: R$ {formatar_moeda(total_estimado)}\n"
    mensagem += f"Frete: R$ {formatar_moeda(orcamento.valor_frete)} ({orcamento.frete_descricao})\n"
    mensagem += f"Total estimado com frete: R$ {formatar_moeda(orcamento.total_estimado)}\n"

    mensagem += "\nEntrega:\n"
    mensagem += f"Forma: {orcamento.forma_entrega}\n"
    if orcamento.cep_entrega:
        mensagem += f"CEP: {orcamento.cep_entrega}\n"

    if orcamento.arte:
        mensagem += "\nArte/logo enviada:\n"
        mensagem += f"{request.build_absolute_uri(orcamento.arte.url)}\n"
    else:
        mensagem += "\nArte/logo: vou enviar ou explicar no WhatsApp.\n"

    if orcamento.observacao:
        mensagem += f"\nObservacoes: {orcamento.observacao}\n"

    mensagem += "\nEntendo que o valor pode passar por confirmacao conforme a complexidade da arte."

    return JsonResponse({
        "whatsapp_url": (
            f"https://wa.me/{NUMERO_WHATSAPP_ATENDIMENTO}"
            f"?text={quote(mensagem)}"
        )
    }, status=201)


def universitarios(request):
    produtos_base = Produto.objects.filter(categoria='Universitário')
    cursos = list(
        produtos_base
        .exclude(curso='')
        .order_by('curso')
        .values_list('curso', flat=True)
        .distinct()
    )
    curso_selecionado = request.GET.get('curso', '').strip()
    produtos = produtos_base

    if curso_selecionado:
        produtos = produtos.filter(curso__iexact=curso_selecionado)

    produtos = produtos_com_fotos(produtos)

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
        'mostrar_filtro_cursos': True,
        'filtro_cursos': cursos,
        'curso_selecionado': curso_selecionado,
    })


def empresariais(request):
    return redirect('home')

def produto_detalhe(request, id):
    produto = get_object_or_404(
        produtos_com_fotos(Produto.objects.all()),
        id=id
    )
    fotos_produto = getattr(produto, 'fotos_ativas', [])

    return render(request, 'loja/produto.html', {
        'produto': produto,
        'fotos_produto': fotos_produto
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
    ).select_related('produto').prefetch_related(
        Prefetch(
            'produto__fotos',
            queryset=ProdutoFoto.objects.filter(ativo=True).order_by('ordem', 'id'),
            to_attr='fotos_ativas'
        )
    )

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
    modelagem = request.GET.get('modelagem', '')

    if not tamanho or not cor or not modelagem:
        return redirect('produto_detalhe', id=id)

    chave = f"{id}_{tamanho}_{cor}_{modelagem}"

    if chave in carrinho:
        carrinho[chave]['quantidade'] += quantidade
    else:
        carrinho[chave] = {
            'produto_id': produto.id,
            'quantidade': quantidade,
            'tamanho': tamanho,
            'cor': cor,
            'modelagem': modelagem
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
            'modelagem': dados.get('modelagem', ''),
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
    tem_produto_personalizado = False

    for chave, dados in carrinho.items():
        produto = get_object_or_404(Produto, id=dados['produto_id'])
        quantidade = dados['quantidade']
        subtotal = produto.preco * quantidade
        subtotal_pedido += subtotal
        total_itens += quantidade
        tem_produto_personalizado = (
            tem_produto_personalizado or produto.categoria == "Personalizado"
        )

        produtos.append({
            'chave': chave,
            'produto': produto,
            'quantidade': quantidade,
            'tamanho': dados.get('tamanho', ''),
            'cor': dados.get('cor', ''),
            'modelagem': dados.get('modelagem', ''),
            'subtotal': subtotal
        })
    if request.method == 'POST':
        nome_cliente = request.POST.get('nome_cliente', '').strip()
        telefone = formatar_telefone(request.POST.get('telefone', '').strip())
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

        curso = request.POST.get('curso', '') if tem_produto_personalizado else ''
        nome_bordado = request.POST.get('nome_bordado', '') if tem_produto_personalizado else ''
        observacao_item = request.POST.get('observacao_item', '') if tem_produto_personalizado else ''

        arte = request.FILES.get('arte') if tem_produto_personalizado else None

        campos_cliente = {
            "nome completo": nome_cliente,
            "telefone/WhatsApp": telefone,
        }
        campos_cliente_faltando = [
            nome for nome, valor in campos_cliente.items() if not valor
        ]

        if campos_cliente_faltando:
            campos = ", ".join(campos_cliente_faltando)
            messages.error(
                request,
                f"Preencha os campos obrigatorios do cliente: {campos}."
            )
            return redirect('checkout')

        if forma_entrega not in FORMAS_ENTREGA:
            messages.error(request, 'Escolha uma forma de entrega valida.')
            return redirect('checkout')

        if forma_pagamento not in FORMAS_PAGAMENTO:
            messages.error(request, 'Escolha uma forma de pagamento valida.')
            return redirect('checkout')

        if forma_entrega == "Entrega":
            campos_entrega = {
                "CEP": cep_entrega,
                "endereco": endereco,
                "numero": numero,
                "bairro": bairro,
                "cidade": cidade,
                "estado": estado,
            }
            campos_faltando = [
                nome for nome, valor in campos_entrega.items() if not valor
            ]

            if campos_faltando:
                campos = ", ".join(campos_faltando)
                messages.error(
                    request,
                    f"Preencha os campos obrigatorios da entrega: {campos}."
                )
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
            item_personalizado = item['produto'].categoria == "Personalizado"
            curso_item = curso if item_personalizado else ''
            nome_bordado_item = nome_bordado if item_personalizado else ''
            observacao_item_final = observacao_item if item_personalizado else ''
            arte_item = arte if item_personalizado else None

            ItemPedido.objects.create(
                pedido=pedido,
                produto=item['produto'],
                quantidade=item['quantidade'],
                tamanho=item['tamanho'],
                cor=item['cor'],
                modelagem=item['modelagem'],
                curso=curso_item,
                nome_bordado=nome_bordado_item,
                observacao=observacao_item_final,
                arte=arte_item,
                subtotal=item['subtotal']
            )

            mensagem += f"- {item['produto'].nome}\n"
            mensagem += f"  Tamanho: {item['tamanho']}\n"
            mensagem += f"  Cor: {item['cor']}\n"
            if item['modelagem']:
                mensagem += f"  Modelagem: {item['modelagem']}\n"
            mensagem += f"  Quantidade: {item['quantidade']}\n"

            if curso_item:
                mensagem += f"  Curso/Turma/Empresa: {curso_item}\n"

            if nome_bordado_item:
                mensagem += f"  Nome bordado: {nome_bordado_item}\n"

            if observacao_item_final:
                mensagem += f"  Detalhes do bordado: {observacao_item_final}\n"

            if arte_item:
                mensagem += "  Arte/logo enviada no pedido.\n"

            mensagem += f"  Subtotal: R$ {item['subtotal']:.2f}\n\n"

        mensagem += f"Subtotal dos produtos: R$ {formatar_moeda(subtotal_pedido)}\n"
        mensagem += f"Frete: R$ {formatar_moeda(frete['valor'])} ({frete['descricao']})\n"
        if forma_entrega == "Entrega":
            mensagem += f"Prazo: {OBSERVACAO_PRAZO_ENTREGA}\n"
        mensagem += f"Total: R$ {formatar_moeda(total_final)}\n\n"
        mensagem += "Aguardo o atendimento."

        request.session['carrinho'] = {}
        request.session['ultimo_pedido_id'] = pedido.id

        if forma_pagamento in PAGAMENTOS_ONLINE:
            return redirect('pagamento_pedido', pedido_id=pedido.id)

        texto = quote(mensagem)
        numero_whatsapp = NUMERO_WHATSAPP_ATENDIMENTO

        return redirect(f"https://wa.me/{numero_whatsapp}?text={texto}")

    return render(request, 'loja/checkout.html', {
        'itens': produtos,
        'subtotal': subtotal_pedido,
        'total': subtotal_pedido,
        'total_itens': total_itens,
        'formas_pagamento': FORMAS_PAGAMENTO,
        'tem_produto_personalizado': tem_produto_personalizado,
    })


def pagamento_pedido(request, pedido_id):
    pedido = get_object_or_404(
        Pedido.objects.prefetch_related("itens__produto"),
        id=pedido_id
    )

    if pedido.usuario_id:
        if not request.user.is_authenticated:
            return redirect('login')

        if pedido.usuario_id != request.user.id:
            return redirect('home')
    elif request.session.get('ultimo_pedido_id') != pedido.id:
        return redirect('home')

    pix_codigo = ""
    pix_qrcode_url = ""

    if pedido.forma_pagamento == "Pix":
        pix_codigo = gerar_codigo_pix(pedido)
        if pix_codigo:
            pix_qrcode_url = (
                "https://api.qrserver.com/v1/create-qr-code/"
                f"?size=280x280&data={quote(pix_codigo)}"
            )

    mercado_pago_url = ""

    if pedido.forma_pagamento in PAGAMENTOS_ONLINE:
        mercado_pago_url = criar_preferencia_mercado_pago(pedido, request)

    return render(request, 'loja/pagamento.html', {
        'pedido': pedido,
        'pix_codigo': pix_codigo,
        'pix_qrcode_url': pix_qrcode_url,
        'pix_configurado': bool(settings.PIX_CHAVE.strip()),
        'mercado_pago_url': mercado_pago_url,
        'mercado_pago_configurado': bool(settings.MERCADO_PAGO_ACCESS_TOKEN.strip()),
        'whatsapp_url': montar_link_whatsapp_pedido(pedido),
        'status_retorno': request.GET.get('status', ''),
    })


@csrf_exempt
def mercado_pago_webhook(request):
    if request.method != "POST":
        return JsonResponse({"erro": "metodo nao permitido"}, status=405)

    try:
        payload = request.body.decode("utf-8")
        dados = json.loads(payload) if payload else {}
    except ValueError:
        dados = {}

    tipo = dados.get("type") or dados.get("topic") or request.GET.get("type")
    pagamento_id = (
        (dados.get("data") or {}).get("id")
        or request.GET.get("data.id")
        or request.GET.get("id")
    )

    if tipo == "payment" and pagamento_id:
        atualizar_pedido_por_pagamento_mercado_pago(pagamento_id)

    return JsonResponse({"recebido": True})


def cadastro(request):
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        email = request.POST.get('email', '').strip()
        senha = request.POST.get('senha', '')
        senha_confirmacao = request.POST.get('senha_confirmacao', '')

        if not nome or not email or not senha:
            messages.error(request, 'Preencha nome, e-mail e senha para criar sua conta.')
            return redirect('cadastro')

        if senha != senha_confirmacao:
            messages.error(request, 'As senhas nao conferem. Digite a mesma senha nos dois campos.')
            return redirect('cadastro')

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
