from django.db import migrations, models


def fill_weekday_hours(apps, schema_editor):
    UserPayrollProfile = apps.get_model('shopCRM', 'UserPayrollProfile')
    for profile in UserPayrollProfile.objects.all():
        base = profile.hours_per_day
        profile.monday_hours = base
        profile.tuesday_hours = base
        profile.wednesday_hours = base
        profile.thursday_hours = base
        profile.friday_hours = base
        profile.saturday_hours = 0
        profile.sunday_hours = 0
        profile.save(update_fields=[
            'monday_hours',
            'tuesday_hours',
            'wednesday_hours',
            'thursday_hours',
            'friday_hours',
            'saturday_hours',
            'sunday_hours',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('shopCRM', '0008_userpayrollprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userpayrollprofile',
            name='friday_hours',
            field=models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name='Пт год'),
        ),
        migrations.AddField(
            model_name='userpayrollprofile',
            name='monday_hours',
            field=models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name='Пн год'),
        ),
        migrations.AddField(
            model_name='userpayrollprofile',
            name='saturday_hours',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Сб год'),
        ),
        migrations.AddField(
            model_name='userpayrollprofile',
            name='sunday_hours',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5, verbose_name='Нд год'),
        ),
        migrations.AddField(
            model_name='userpayrollprofile',
            name='thursday_hours',
            field=models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name='Чт год'),
        ),
        migrations.AddField(
            model_name='userpayrollprofile',
            name='tuesday_hours',
            field=models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name='Вт год'),
        ),
        migrations.AddField(
            model_name='userpayrollprofile',
            name='wednesday_hours',
            field=models.DecimalField(decimal_places=2, default=8, max_digits=5, verbose_name='Ср год'),
        ),
        migrations.RunPython(fill_weekday_hours, migrations.RunPython.noop),
    ]
