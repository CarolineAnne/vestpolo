import hashlib
import json

from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from .melhor_envio import MelhorEnvioClient, MelhorEnvioError, primeiro_valor
from .models import Produto, ProdutoFoto, Pedido, ItemPedido, Favorito, AdicionalPersonalizacao

@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'produto', 'data_adicionado')
    search_fields = ('usuario__username', 'produto__nome')
    list_filter = ('data_adicionado',)


class ProdutoFotoInline(admin.TabularInline):
    model = ProdutoFoto
    extra = 1
    fields = ('preview', 'imagem', 'titulo', 'ordem', 'ativo')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj and obj.imagem:
            return format_html(
                '<img src="{}" style="width:80px;height:80px;object-fit:cover;border-radius:8px;border:1px solid #ddd;">',
                obj.imagem.url
            )
        return 'Sem foto'

    preview.short_description = 'Previa'


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'miniatura', 'nome', 'categoria', 'curso', 'preco')
    search_fields = ('nome', 'descricao', 'curso')
    list_filter = ('categoria', 'curso')
    list_per_page = 20
    readonly_fields = ('preview_imagem',)
    inlines = [ProdutoFotoInline]

    fieldsets = (
        ('Dados principais', {
            'fields': (
                'nome',
                'preco',
                'descricao',
                'categoria',
                'curso',
            )
        }),
        ('Foto principal', {
            'fields': (
                'preview_imagem',
                'imagem',
            )
        }),
        ('Fotos por cor', {
            'fields': (
                ('imagem_preta', 'imagem_preta_costas'),
                ('imagem_branca', 'imagem_branca_costas'),
                ('imagem_vinho', 'imagem_vinho_costas'),
                ('imagem_marinho', 'imagem_marinho_costas'),
                ('imagem_amarelo', 'imagem_amarelo_costas'),
                ('imagem_verde', 'imagem_verde_costas'),
            )
        }),
        ('Imagens de apoio', {
            'fields': (
                'imagem_logo',
                'imagem_tamanho',
                'imagem_tamanho_feminino',
                'imagem_tamanho_masculino',
            )
        }),
    )

    def miniatura(self, obj):
        imagem = obj.imagem_vitrine

        if imagem:
            return format_html(
                '<img src="{}" style="width:54px;height:54px;object-fit:cover;border-radius:8px;border:1px solid #ddd;">',
                imagem
            )

        return '-'

    miniatura.short_description = 'Foto'

    def preview_imagem(self, obj):
        if obj and obj.imagem:
            return format_html(
                '<img src="{}" style="max-width:220px;max-height:220px;object-fit:contain;border-radius:8px;border:1px solid #ddd;background:#fff;">',
                obj.imagem.url
            )

        return 'Nenhuma foto principal cadastrada.'

    preview_imagem.short_description = 'Previa da foto principal'


@admin.register(ProdutoFoto)
class ProdutoFotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'preview', 'produto', 'titulo', 'ordem', 'ativo')
    list_editable = ('ordem', 'ativo')
    search_fields = ('produto__nome', 'titulo')
    list_filter = ('ativo', 'produto__categoria')
    autocomplete_fields = ('produto',)
    list_per_page = 30

    def preview(self, obj):
        if obj.imagem:
            return format_html(
                '<img src="{}" style="width:58px;height:58px;object-fit:cover;border-radius:8px;border:1px solid #ddd;">',
                obj.imagem.url
            )
        return '-'

    preview.short_description = 'Foto'


@admin.register(AdicionalPersonalizacao)
class AdicionalPersonalizacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'ativo', 'ordem')
    list_editable = ('preco', 'ativo', 'ordem')
    search_fields = ('nome', 'descricao')
    list_filter = ('ativo',)
    ordering = ('ordem', 'nome')


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    
    readonly_fields = (
        'produto',
        'quantidade',
        'tamanho',
        'cor',
        'modelagem',
        'curso',
        'nome_bordado',
        'observacao',
        'arte',
        'subtotal',
    )

    fields = (
        'produto',
        'quantidade',
        'tamanho',
        'cor',
        'modelagem',
        'curso',
        'nome_bordado',
        'observacao',
        'arte',
        'subtotal',
    )

    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    change_form_template = 'admin/loja/pedido/change_form.html'

    list_display = (
        'id',
        'nome_cliente',
        'telefone',
        'forma_entrega',
        'forma_pagamento',
        'valor_frete',
        'status',
        'status_pagamento',
        'total',
        'data_pedido',
        'imprimir_envio',
        'imprimir_etiqueta',
        'melhor_envio_acesso',
    )

    list_editable = ('status', 'status_pagamento')

    list_filter = (
        'status',
        'status_pagamento',
        'forma_entrega',
        'forma_pagamento',
        'data_pedido',
    )

    search_fields = (
        'id',
        'nome_cliente',
        'telefone',
        'observacao',
        'codigo_rastreio',
        'melhor_envio_id',
    )

    readonly_fields = (
        'data_pedido',
        'imprimir_envio',
        'imprimir_etiqueta',
        'melhor_envio_acesso',
        'melhor_envio_atualizado_em',
        'melhor_envio_erro',
    )

    fieldsets = (
        ('Dados do cliente', {
            'fields': (
                'nome_cliente',
                'telefone',
                'forma_entrega',
                'forma_pagamento',
                'observacao',
            )
        }),

        ('Endereco de entrega', {
            'fields': (
                'cep_entrega',
                'endereco',
                'numero',
                'complemento',
                'bairro',
                'cidade',
                'estado',
            )
        }),

        ('Dados do pedido', {
            'fields': (
                'subtotal',
                'valor_frete',
                'transportadora',
                'servico_frete',
                'prazo_entrega',
                'total',
                'status',
                'status_pagamento',
                'mercado_pago_id',
                'data_pedido',
                'imprimir_envio',
                'imprimir_etiqueta',
            )
        }),

        ('Melhor Envio', {
            'fields': (
                'melhor_envio_acesso',
                'melhor_envio_id',
                'melhor_envio_status',
                'codigo_rastreio',
                'melhor_envio_etiqueta_url',
                'melhor_envio_atualizado_em',
                'melhor_envio_erro',
            )
        }),
    )

    inlines = [ItemPedidoInline]

    list_per_page = 20

    ordering = ('-data_pedido',)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:pedido_id>/imprimir-envio/',
                self.admin_site.admin_view(self.imprimir_envio_view),
                name='loja_pedido_imprimir_envio',
            ),
            path(
                '<int:pedido_id>/etiqueta-correios/',
                self.admin_site.admin_view(self.etiqueta_correios_view),
                name='loja_pedido_etiqueta_correios',
            ),
            path(
                '<int:pedido_id>/melhor-envio/',
                self.admin_site.admin_view(self.melhor_envio_view),
                name='loja_pedido_melhor_envio',
            ),
        ]
        return custom_urls + urls

    def imprimir_envio(self, obj):
        if not obj or not obj.id:
            return '-'

        url = reverse('admin:loja_pedido_imprimir_envio', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" target="_blank">Imprimir envio</a>',
            url
        )

    imprimir_envio.short_description = 'Correios'

    def imprimir_etiqueta(self, obj):
        if not obj or not obj.id:
            return '-'

        url = reverse('admin:loja_pedido_etiqueta_correios', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" target="_blank">Etiqueta Correios</a>',
            url
        )

    imprimir_etiqueta.short_description = 'Etiqueta'

    def melhor_envio_acesso(self, obj):
        if not obj or not obj.id:
            return '-'

        url = reverse('admin:loja_pedido_melhor_envio', args=[obj.id])
        texto = 'Melhor Envio'

        if obj.codigo_rastreio:
            texto = obj.codigo_rastreio
        elif obj.melhor_envio_status:
            texto = obj.melhor_envio_status

        return format_html(
            '<a class="button" href="{}" target="_blank">{}</a>',
            url,
            texto
        )

    melhor_envio_acesso.short_description = 'Melhor Envio'

    def imprimir_envio_view(self, request, pedido_id):
        pedido = get_object_or_404(
            Pedido.objects.prefetch_related('itens__produto'),
            id=pedido_id
        )

        context = {
            **self.admin_site.each_context(request),
            'title': f'Imprimir envio - Pedido #{pedido.id}',
            'pedido': pedido,
        }
        return render(request, 'admin/loja/pedido/imprimir_envio.html', context)

    def _codigo_etiqueta_interno(self, pedido):
        return f"VP{pedido.id:09d}"

    def _gerar_barras_etiqueta(self, seed, quantidade=84):
        digest = hashlib.sha256(str(seed).encode('utf-8')).digest()
        barras = []

        for indice in range(quantidade):
            byte = digest[indice % len(digest)]
            largura = 1 + ((byte + indice) % 4)
            barras.append({
                'ativo': indice % 2 == 0,
                'largura': largura,
            })

        return barras

    def _gerar_matriz_etiqueta(self, seed, tamanho=17):
        digest = hashlib.sha256(str(seed).encode('utf-8')).digest()
        matriz = []

        for linha in range(tamanho):
            colunas = []
            for coluna in range(tamanho):
                borda = (
                    linha == 0 or
                    coluna == 0 or
                    linha == tamanho - 1 or
                    coluna == tamanho - 1
                )
                valor = digest[(linha * tamanho + coluna) % len(digest)]
                colunas.append(borda or ((valor + linha + coluna) % 3 == 0))
            matriz.append(colunas)

        return matriz

    def etiqueta_correios_view(self, request, pedido_id):
        pedido = get_object_or_404(
            Pedido.objects.prefetch_related('itens__produto'),
            id=pedido_id
        )

        codigo_interno = pedido.codigo_rastreio or self._codigo_etiqueta_interno(pedido)
        cep_destino = ''.join(filter(str.isdigit, pedido.cep_entrega or ''))

        context = {
            **self.admin_site.each_context(request),
            'title': f'Etiqueta Correios - Pedido #{pedido.id}',
            'pedido': pedido,
            'codigo_interno': codigo_interno,
            'tem_rastreio_real': bool(pedido.codigo_rastreio),
            'barras_principais': self._gerar_barras_etiqueta(codigo_interno, 92),
            'barras_destino': self._gerar_barras_etiqueta(cep_destino or codigo_interno, 58),
            'matriz_etiqueta': self._gerar_matriz_etiqueta(codigo_interno),
        }
        return render(request, 'admin/loja/pedido/etiqueta_correios.html', context)

    def melhor_envio_view(self, request, pedido_id):
        pedido = get_object_or_404(
            Pedido.objects.prefetch_related('itens__produto'),
            id=pedido_id
        )

        client = MelhorEnvioClient()

        if request.method == 'POST':
            acao = request.POST.get('acao')

            try:
                if acao == 'criar_carrinho':
                    self._melhor_envio_criar_carrinho(pedido, client)
                    messages.success(request, 'Envio criado no carrinho do Melhor Envio.')

                elif acao == 'gerar_etiqueta':
                    self._melhor_envio_gerar_etiqueta(pedido, client)
                    messages.success(request, 'Solicitacao de geracao de etiqueta enviada.')

                elif acao == 'imprimir_etiqueta':
                    self._melhor_envio_imprimir_etiqueta(pedido, client)
                    messages.success(request, 'Link de impressao da etiqueta atualizado.')

                elif acao == 'consultar':
                    self._melhor_envio_consultar(pedido, client)
                    messages.success(request, 'Dados consultados no Melhor Envio.')

                else:
                    messages.warning(request, 'Acao nao reconhecida.')

            except MelhorEnvioError as exc:
                pedido.melhor_envio_erro = str(exc)
                pedido.melhor_envio_atualizado_em = timezone.now()
                pedido.save(update_fields=['melhor_envio_erro', 'melhor_envio_atualizado_em'])
                messages.error(request, str(exc))

            return redirect(reverse('admin:loja_pedido_melhor_envio', args=[pedido.id]))

        context = {
            **self.admin_site.each_context(request),
            'title': f'Melhor Envio - Pedido #{pedido.id}',
            'pedido': pedido,
            'melhor_envio_configurado': client.configurado(),
        }
        return render(request, 'admin/loja/pedido/melhor_envio.html', context)

    def _melhor_envio_criar_carrinho(self, pedido, client):
        self._validar_pedido_melhor_envio(pedido)
        data = client.criar_envio_no_carrinho(pedido)
        self._atualizar_pedido_melhor_envio(pedido, data)

    def _melhor_envio_gerar_etiqueta(self, pedido, client):
        self._exigir_melhor_envio_id(pedido)
        data = client.gerar_etiqueta(pedido.melhor_envio_id)
        self._atualizar_pedido_melhor_envio(pedido, data)

    def _melhor_envio_imprimir_etiqueta(self, pedido, client):
        self._exigir_melhor_envio_id(pedido)
        data = client.imprimir_etiqueta(pedido.melhor_envio_id)
        self._atualizar_pedido_melhor_envio(pedido, data)

    def _melhor_envio_consultar(self, pedido, client):
        self._exigir_melhor_envio_id(pedido)
        data = client.consultar_envio(pedido.melhor_envio_id)
        self._atualizar_pedido_melhor_envio(pedido, data)

    def _validar_pedido_melhor_envio(self, pedido):
        if pedido.forma_entrega != 'Entrega':
            raise MelhorEnvioError('Este pedido nao esta marcado como entrega.')

        obrigatorios = {
            'nome do cliente': pedido.nome_cliente,
            'telefone': pedido.telefone,
            'CEP': pedido.cep_entrega,
            'endereco': pedido.endereco,
            'numero': pedido.numero,
            'bairro': pedido.bairro,
            'cidade': pedido.cidade,
            'estado': pedido.estado,
        }

        faltando = [nome for nome, valor in obrigatorios.items() if not valor]

        if faltando:
            raise MelhorEnvioError('Preencha antes de gerar etiqueta: ' + ', '.join(faltando) + '.')

    def _exigir_melhor_envio_id(self, pedido):
        if not pedido.melhor_envio_id:
            raise MelhorEnvioError('Crie o envio no carrinho do Melhor Envio antes desta acao.')

    def _atualizar_pedido_melhor_envio(self, pedido, data):
        melhor_envio_id = primeiro_valor(data, ('id', 'order_id', 'protocol'))
        status = primeiro_valor(data, ('status', 'status_name', 'state'))
        rastreio = primeiro_valor(data, ('tracking', 'tracking_code', 'codigo_rastreio', 'tracking_number'))
        etiqueta_url = primeiro_valor(data, ('url', 'print_url', 'label_url', 'download_url'))

        if melhor_envio_id and not pedido.melhor_envio_id:
            pedido.melhor_envio_id = melhor_envio_id

        if status:
            pedido.melhor_envio_status = status

        if rastreio:
            pedido.codigo_rastreio = rastreio

        if etiqueta_url:
            pedido.melhor_envio_etiqueta_url = etiqueta_url

        pedido.melhor_envio_erro = json.dumps(data, ensure_ascii=False, indent=2)[:4000]
        pedido.melhor_envio_atualizado_em = timezone.now()
        pedido.save(update_fields=[
            'melhor_envio_id',
            'melhor_envio_status',
            'codigo_rastreio',
            'melhor_envio_etiqueta_url',
            'melhor_envio_erro',
            'melhor_envio_atualizado_em',
        ])

    def response_change(self, request, obj):
        if "_salvar_imprimir_envio" in request.POST:
            return redirect(
                reverse('admin:loja_pedido_imprimir_envio', args=[obj.id])
            )

        if "_salvar_imprimir_etiqueta" in request.POST:
            return redirect(
                reverse('admin:loja_pedido_etiqueta_correios', args=[obj.id])
            )

        if "_salvar_melhor_envio" in request.POST:
            return redirect(
                reverse('admin:loja_pedido_melhor_envio', args=[obj.id])
            )

        return super().response_change(request, obj)
