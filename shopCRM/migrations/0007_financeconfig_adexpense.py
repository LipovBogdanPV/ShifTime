from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shopCRM', '0006_messagetemplate'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinanceConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('manager_hourly_rate', models.DecimalField(decimal_places=2, default=40, max_digits=10, verbose_name='Ставка менеджера за годину')),
                ('manager_hours_per_day', models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name='Годин на день')),
                ('manager_commission_percent', models.DecimalField(decimal_places=2, default=5, max_digits=5, verbose_name='% менеджеру від замовлень')),
                ('fop_fixed_tax_monthly', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Фіксований податок ФОП (місяць)')),
                ('fop_income_tax_percent', models.DecimalField(decimal_places=2, default=5, max_digits=5, verbose_name='% податку від доходу')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
            ],
            options={
                'verbose_name': 'Фінансові налаштування',
                'verbose_name_plural': 'Фінансові налаштування',
            },
        ),
        migrations.CreateModel(
            name='AdExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spend_date', models.DateField(verbose_name='Дата')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сума')),
                ('comment', models.CharField(blank=True, max_length=255, verbose_name='Коментар')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Створено')),
            ],
            options={
                'verbose_name': 'Витрати на рекламу',
                'verbose_name_plural': 'Витрати на рекламу',
                'ordering': ['-spend_date', '-id'],
            },
        ),
    ]
