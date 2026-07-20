from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loja', '0018_produtofoto'),
    ]

    operations = [
        migrations.AddField(
            model_name='produto',
            name='curso',
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
