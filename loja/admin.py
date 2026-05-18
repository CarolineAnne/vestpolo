from django.contrib import admin
from .models import Produto, Pedido, ItemPedido


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco', 'tamanho')
    search_fields = ('nome', 'descricao')
    list_filter = ('tamanho',)


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ('produto', 'quantidade', 'subtotal')
    can_delete = False


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome_cliente', 'telefone', 'status', 'total', 'data_pedido')
    readonly_fields = ('data_pedido',)
    list_filter = ('status', 'data_pedido')
    search_fields = ('id',)
    inlines = [ItemPedidoInline]