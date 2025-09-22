from django.conf import settings
from django.db import migrations, models


def assign_users_to_earnings(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    UserEarnings = apps.get_model('core', 'UserEarnings')

    default_user = User.objects.order_by('id').first()
    if default_user is None:
        return

    available_users = list(User.objects.filter(earnings__isnull=True).order_by('id'))
    user_iterator = iter(available_users)

    for earnings in UserEarnings.objects.filter(user__isnull=True).order_by('id'):
        try:
            user = next(user_iterator)
        except StopIteration:
            user = default_user
        earnings.user = user
        earnings.save(update_fields=['user'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_walletuser'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='userearnings',
            name='user',
            field=models.OneToOneField(null=True, on_delete=models.CASCADE, related_name='earnings', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(assign_users_to_earnings, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='userearnings',
            name='user',
            field=models.OneToOneField(on_delete=models.CASCADE, related_name='earnings', to=settings.AUTH_USER_MODEL),
        ),
    ]
