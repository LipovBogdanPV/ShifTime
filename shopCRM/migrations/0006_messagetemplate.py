from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopCRM', '0005_order_platform_orderitem_cost_price_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True, verbose_name='Назва шаблону')),
                ('body', models.TextField(verbose_name='Текст шаблону')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активний')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
            ],
            options={
                'verbose_name': 'Шаблон повідомлення',
                'verbose_name_plural': 'Шаблони повідомлень',
                'ordering': ['name'],
            },
        ),
    ]
