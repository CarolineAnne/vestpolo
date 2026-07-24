from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0019_produto_curso'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='imagem_tamanho_feminino',
            field=models.ImageField(blank=True, null=True, upload_to='produtos/tamanhos/', verbose_name='Tabela de tamanhos feminino'),
        ),
        migrations.AddField(
            model_name='produto',
            name='imagem_tamanho_masculino',
            field=models.ImageField(blank=True, null=True, upload_to='produtos/tamanhos/', verbose_name='Tabela de tamanhos masculino'),
        ),
    ]
