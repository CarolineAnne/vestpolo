from django.contrib import admin
from .models import Produto, Pedido, ItemPedido, Favorito

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

    readonly_fields = ('data_pedido',)

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
            )
        }),
    )

    inlines = [ItemPedidoInline]

    list_per_page = 20

    ordering = ('-data_pedido',)
