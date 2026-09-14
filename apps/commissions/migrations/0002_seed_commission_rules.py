from decimal import Decimal

from django.db import migrations


def create_rules(apps, schema_editor):
    CommissionRule = apps.get_model("commissions", "CommissionRule")

    CommissionRule.objects.get_or_create(
        role_name="Business Developer",
        defaults={
            "commission_percentage": Decimal("5.00"),
            "is_active": True,
        },
    )

    CommissionRule.objects.get_or_create(
        role_name="Technical Manager",
        defaults={
            "commission_percentage": Decimal("10.00"),
            "is_active": True,
        },
    )


def remove_rules(apps, schema_editor):
    CommissionRule = apps.get_model("commissions", "CommissionRule")

    CommissionRule.objects.filter(
        role_name__in=[
            "Business Developer",
            "Technical Manager",
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("commissions", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_rules,
            remove_rules,
        ),
    ]