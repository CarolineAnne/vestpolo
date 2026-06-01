from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('produto/<int:id>/', views.produto_detalhe, name='produto_detalhe'),
    path('favoritar/<int:id>/', views.favoritar, name='favoritar'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('add-carrinho/<int:id>/', views.adicionar_carrinho, name='add_carrinho'),
    path('remover-carrinho/<str:chave>/', views.remover_carrinho, name='remover_carrinho'),
    path('mais/<str:chave>/', views.aumentar_quantidade, name='mais'),
    path('menos/<str:chave>/', views.diminuir_quantidade, name='menos'),
    path('finalizar-whatsapp/', views.finalizar_whatsapp, name='finalizar_whatsapp'),
    path('checkout/', views.checkout, name='checkout'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('minha-conta/', views.minha_conta, name='minha_conta'),
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
]