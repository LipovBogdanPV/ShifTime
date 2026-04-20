from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shopCRM', '0007_financeconfig_adexpense'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPayrollProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hourly_rate', models.DecimalField(decimal_places=2, default=40, max_digits=10, verbose_name='Ставка за годину')),
                ('hours_per_day', models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name='Годин на день')),
                ('commission_percent', models.DecimalField(decimal_places=2, default=5, max_digits=5, verbose_name='% від замовлень')),
                ('include_in_payroll', models.BooleanField(default=True, verbose_name='Враховувати в нарахуванні')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Оновлено')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='payroll_profile', to='shopCRM.user', verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'Налаштування оплати користувача',
                'verbose_name_plural': 'Налаштування оплат користувачів',
            },
        ),
    ]
