from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0017_itempedido_modelagem'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProdutoFoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('imagem', models.ImageField(upload_to='produtos/galeria/')),
                ('titulo', models.CharField(blank=True, max_length=80, verbose_name='Titulo ou legenda')),
                ('ordem', models.PositiveIntegerField(default=0)),
                ('ativo', models.BooleanField(default=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('produto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fotos', to='loja.produto')),
            ],
            options={
                'verbose_name': 'Foto do produto',
                'verbose_name_plural': 'Fotos do produto',
                'ordering': ('ordem', 'id'),
            },
        ),
    ]
