from decimal import Decimal

from django.db import migrations, models


def criar_adicionais_padrao(apps, schema_editor):
    AdicionalPersonalizacao = apps.get_model('loja', 'AdicionalPersonalizacao')

    adicionais = [
        ('Logo no peito', 'Bordado pequeno no peito', Decimal('15.00'), 1),
        ('Nome bordado', 'Nome ou identificacao individual', Decimal('8.00'), 2),
        ('Logo na manga', 'Bordado pequeno na manga', Decimal('10.00'), 3),
        ('Logo nas costas', 'Logo media nas costas', Decimal('25.00'), 4),
        ('Bordado grande nas costas', 'Bordado maior com mais detalhes', Decimal('35.00'), 5),
    ]

    for nome, descricao, preco, ordem in adicionais:
        AdicionalPersonalizacao.objects.get_or_create(
            nome=nome,
            defaults={
                'descricao': descricao,
                'preco': preco,
                'ordem': ordem,
                'ativo': True,
            },
        )


def remover_adicionais_padrao(apps, schema_editor):
    AdicionalPersonalizacao = apps.get_model('loja', 'AdicionalPersonalizacao')
    nomes = [
        'Logo no peito',
        'Nome bordado',
        'Logo na manga',
        'Logo nas costas',
        'Bordado grande nas costas',
    ]
    AdicionalPersonalizacao.objects.filter(nome__in=nomes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0014_pedido_bairro_pedido_cep_entrega_pedido_cidade_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdicionalPersonalizacao',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('descricao', models.CharField(blank=True, max_length=180)),
                ('preco', models.DecimalField(decimal_places=2, max_digits=10)),
                ('ativo', models.BooleanField(default=True)),
                ('ordem', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Adicional de personalizacao',
                'verbose_name_plural': 'Adicionais de personalizacao',
                'ordering': ('ordem', 'nome'),
            },
        ),
        migrations.RunPython(criar_adicionais_padrao, remover_adicionais_padrao),
    ]
