from django.db import models


class Produto(models.Model):
    CATEGORIAS = [
        ('Universitário', 'Universitário'),
        ('Empresarial', 'Empresarial'),
        ('Personalizado', 'Personalizado'),
    ]
    
    nome = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.TextField(blank=True)

    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIAS,
        default='Universitário'
    )

    imagem = models.ImageField(
        upload_to='produtos/',
        blank=True,
        null=True
    )

    imagem_preta = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_preta_costas = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)

    imagem_branca = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_branca_costas = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)

    imagem_vinho = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_vinho_costas = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)

    imagem_marinho = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_marinho_costas = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)

    imagem_amarelo = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_amarelo_costas = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)

    imagem_verde = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_verde_costas = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)

    imagem_logo = models.ImageField(
        upload_to='produtos/logos/',
        blank=True,
        null=True,
        verbose_name='Logo do bordado'
    )

    imagem_tamanho = models.ImageField(
        upload_to='produtos/tamanhos/',
        blank=True,
        null=True,
        verbose_name='Tabela de tamanhos'
    )

    def __str__(self):
        return self.nome


class AdicionalPersonalizacao(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.CharField(max_length=180, blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    ativo = models.BooleanField(default=True)
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('ordem', 'nome')
        verbose_name = 'Adicional de personalizacao'
        verbose_name_plural = 'Adicionais de personalizacao'

    def __str__(self):
        return self.nome


class Pedido(models.Model):

    STATUS_CHOICES = [
        ("Pendente", "Pendente"),
        ("Em produção", "Em produção"),
        ("Finalizado", "Finalizado"),
        ("Cancelado", "Cancelado"),
    ]

    STATUS_PAGAMENTO_CHOICES = [
        ("Pendente", "Pendente"),
        ("Aprovado", "Aprovado"),
        ("Recusado", "Recusado"),
        ("Cancelado", "Cancelado"),
        ("Reembolsado", "Reembolsado"),
    ]

    usuario = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    nome_cliente = models.CharField(
        max_length=100,
        blank=True
    )

    telefone = models.CharField(
        max_length=20,
        blank=True
    )

    forma_entrega = models.CharField(
        max_length=50,
        blank=True
    )

    cep_entrega = models.CharField(
        max_length=9,
        blank=True
    )

    endereco = models.CharField(
        max_length=150,
        blank=True
    )

    numero = models.CharField(
        max_length=20,
        blank=True
    )

    complemento = models.CharField(
        max_length=100,
        blank=True
    )

    bairro = models.CharField(
        max_length=100,
        blank=True
    )

    cidade = models.CharField(
        max_length=100,
        blank=True
    )

    estado = models.CharField(
        max_length=2,
        blank=True
    )

    observacao = models.TextField(
        blank=True
    )

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    valor_frete = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    transportadora = models.CharField(
        max_length=100,
        blank=True
    )

    servico_frete = models.CharField(
        max_length=100,
        blank=True
    )

    prazo_entrega = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pendente"
    )

    status_pagamento = models.CharField(
        max_length=20,
        choices=STATUS_PAGAMENTO_CHOICES,
        default="Pendente"
    )

    forma_pagamento = models.CharField(
        max_length=50,
        blank=True
    )

    mercado_pago_id = models.CharField(
        max_length=100,
        blank=True
    )

    melhor_envio_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='ID Melhor Envio'
    )

    melhor_envio_status = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Status Melhor Envio'
    )

    codigo_rastreio = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Codigo de rastreio'
    )

    melhor_envio_etiqueta_url = models.URLField(
        blank=True,
        verbose_name='Link da etiqueta Melhor Envio'
    )

    melhor_envio_erro = models.TextField(
        blank=True,
        verbose_name='Ultimo retorno/erro Melhor Envio'
    )

    melhor_envio_atualizado_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Atualizado no Melhor Envio em'
    )

    data_pedido = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Pedido #{self.id} - {self.status}"


class ItemPedido(models.Model):

    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name='itens'
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE
    )

    quantidade = models.PositiveIntegerField(default=1)
    
    tamanho = models.CharField(max_length=5, blank=True)
    cor = models.CharField(max_length=50, blank=True)
    modelagem = models.CharField(max_length=20, blank=True)
    curso = models.CharField(max_length=100, blank=True)
    nome_bordado = models.CharField(max_length=100, blank=True)
    observacao = models.TextField(blank=True)
    arte = models.FileField(upload_to='artes/', blank=True, null=True)

    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return f"{self.produto.nome} - {self.quantidade} un."


class Favorito(models.Model):

    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
    )

    produto = models.ForeignKey(
        Produto,
        on_delete=models.CASCADE,
    )

    data_adicionado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'produto')

    def __str__(self):
        return f"{self.usuario.username} - {self.produto.nome}"
