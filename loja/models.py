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
    imagem_branca = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_vinho = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_marinho = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_azul = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_amarelo = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)
    imagem_verde = models.ImageField(upload_to='produtos/cores/', blank=True, null=True)

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


class Pedido(models.Model):

    STATUS_CHOICES = [
        ('Pendente', 'Pendente'),
        ('Em produção', 'Em produção'),
        ('Finalizado', 'Finalizado'),
        ('Cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    nome_cliente = models.CharField(max_length=100, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    forma_entrega = models.CharField(max_length=50, blank=True)
    observacao = models.TextField(blank=True)

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pendente'
    )

    data_pedido = models.DateTimeField(auto_now_add=True)

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