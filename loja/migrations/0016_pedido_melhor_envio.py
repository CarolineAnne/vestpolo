from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0015_adicionalpersonalizacao'),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='melhor_envio_id',
            field=models.CharField(blank=True, max_length=100, verbose_name='ID Melhor Envio'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='melhor_envio_status',
            field=models.CharField(blank=True, max_length=80, verbose_name='Status Melhor Envio'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='codigo_rastreio',
            field=models.CharField(blank=True, max_length=80, verbose_name='Codigo de rastreio'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='melhor_envio_etiqueta_url',
            field=models.URLField(blank=True, verbose_name='Link da etiqueta Melhor Envio'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='melhor_envio_erro',
            field=models.TextField(blank=True, verbose_name='Ultimo retorno/erro Melhor Envio'),
        ),
        migrations.AddField(
            model_name='pedido',
            name='melhor_envio_atualizado_em',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Atualizado no Melhor Envio em'),
        ),
    ]
