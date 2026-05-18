from django.contrib import admin
from .models import Produto, Pedido, ItemPedido


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'preco', 'tamanho')
    search_fields = ('nome', 'descricao')
    list_filter = ('tamanho',)
    list_per_page = 20


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('produto', 'quantidade', 'subtotal')
    fields = ('produto', 'quantidade', 'subtotal')
    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nome_cliente',
        'telefone',
        'forma_entrega',
        'status',
        'total',
        'data_pedido',
    )

    list_editable = ('status',)

    list_filter = (
        'status',
        'forma_entrega',
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
                'observacao',
            )
        }),

        ('Dados do pedido', {
            'fields': (
                'total',
                'status',
                'data_pedido',
            )
        }),
    )

    inlines = [ItemPedidoInline]

    list_per_page = 20

    ordering = ('-data_pedido',)