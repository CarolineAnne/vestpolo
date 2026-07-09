from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
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
    path('pagamento/<int:pedido_id>/', views.pagamento_pedido, name='pagamento_pedido'),
    path('mercado-pago/webhook/', views.mercado_pago_webhook, name='mercado_pago_webhook'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_usuario, name='login'),
    path('logout/', views.logout_usuario, name='logout'),
    path('minha-conta/', views.minha_conta, name='minha_conta'),
    path('meus-pedidos/', views.meus_pedidos, name='meus_pedidos'),
    path('personalizados/', views.personalizados, name='personalizados'),
    path('universitarios/', views.universitarios, name='universitarios'),
    path('empresariais/', views.empresariais, name='empresariais'),

    path(
        'esqueci-senha/',
        auth_views.PasswordResetView.as_view(
            template_name='loja/esqueci_senha.html',
            email_template_name='loja/email_recuperacao_senha.html',
            subject_template_name='loja/assunto_recuperacao_senha.txt',
            success_url=reverse_lazy('password_reset_done')
        ),
        name='password_reset'
    ),

    path(
        'esqueci-senha/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='loja/esqueci_senha_enviado.html'
        ),
        name='password_reset_done'
    ),

    path(
        'redefinir-senha/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='loja/redefinir_senha.html',
            success_url=reverse_lazy('password_reset_complete')
        ),
        name='password_reset_confirm'
    ),

    path(
        'senha-redefinida/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='loja/senha_redefinida.html'
        ),
        name='password_reset_complete'
    ),
]
