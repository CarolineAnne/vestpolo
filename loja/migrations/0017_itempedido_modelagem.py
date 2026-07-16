from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0016_pedido_melhor_envio'),
    ]

    operations = [
        migrations.AddField(
            model_name='itempedido',
            name='modelagem',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
