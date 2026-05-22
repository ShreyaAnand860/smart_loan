from django.db import migrations, models


def normalize_roles(apps, schema_editor):
    User = apps.get_model("api", "User")
    User.objects.filter(role__in=["OFFICER", "ADMIN"]).update(role="LOAN_OFFICER")


def restore_legacy_roles(apps, schema_editor):
    User = apps.get_model("api", "User")
    User.objects.filter(role="LOAN_OFFICER").update(role="OFFICER")


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(normalize_roles, restore_legacy_roles),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[("CUSTOMER", "Customer"), ("LOAN_OFFICER", "Loan Officer")],
                default="CUSTOMER",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="loanapplication",
            name="reviewed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]