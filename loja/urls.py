from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('produto/<int:id>/', views.produto_detalhe, name='produto_detalhe'),
    path('favoritar/<int:id>/', views.favoritar, name='favoritar'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('carrinho/', views.carrinho, name='carrinho'),
    path('add-carrinho/<int:id>/', views.adicionar_carrinho, name='add_carrinho'),
    path('remover-carrinho/<int:id>/', views.remover_carrinho, name='remover_carrinho'),
    path('mais/<int:id>/', views.aumentar_quantidade, name='mais'),
    path('menos/<int:id>/', views.diminuir_quantidade, name='menos'),
]