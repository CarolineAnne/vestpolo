from django.contrib import admin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Produto, Pedido, ItemPedido, Favorito, AdicionalPersonalizacao

@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'produto', 'data_adicionado')
    search_fields = ('usuario__username', 'produto__nome')
    list_filter = ('data_adicionado',)


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'categoria', 'preco')
    search_fields = ('nome', 'descricao')
    list_filter = ('categoria',)
    list_per_page = 20


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
    )

    readonly_fields = ('data_pedido', 'imprimir_envio', 'imprimir_etiqueta')

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
            '<a class="button" href="{}" target="_blank">Etiqueta fina</a>',
            url
        )

    imprimir_etiqueta.short_description = 'Etiqueta'

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

    def etiqueta_correios_view(self, request, pedido_id):
        pedido = get_object_or_404(
            Pedido.objects.prefetch_related('itens__produto'),
            id=pedido_id
        )

        context = {
            **self.admin_site.each_context(request),
            'title': f'Etiqueta Correios - Pedido #{pedido.id}',
            'pedido': pedido,
        }
        return render(request, 'admin/loja/pedido/etiqueta_correios.html', context)

    def response_change(self, request, obj):
        if "_salvar_imprimir_envio" in request.POST:
            return redirect(
                reverse('admin:loja_pedido_imprimir_envio', args=[obj.id])
            )

        if "_salvar_imprimir_etiqueta" in request.POST:
            return redirect(
                reverse('admin:loja_pedido_etiqueta_correios', args=[obj.id])
            )

        return super().response_change(request, obj)
