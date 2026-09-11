from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from .models import CommissionRule, CommissionRecord


def calculate_commissions_for_sale(project):
    """
    Called when a Lead converts to a Project.

    Commission is calculated from the sale amount:

        Business Developer -> 5%
        Technical Manager  -> 10%

    The BD is the user who created the lead.

    Technical Managers are users who actually accepted a phase
    of this lead.
    """

    from apps.accounts.roles import Roles
    from apps.leads.models import PhaseManagerHistory

    lead = project.lead
    sale_amount = project.sale_amount

    with transaction.atomic():
        records = []

        # ---------------------------------------------------------
        # Business Developer
        # ---------------------------------------------------------

        bd_user = lead.created_by

        bd_rule = CommissionRule.objects.filter(
            role_name=Roles.BUSINESS_DEVELOPER,
            is_active=True,
        ).first()

        if bd_rule and bd_user:
            records.append(
                _build_record(
                    project=project,
                    user=bd_user,
                    rule=bd_rule,
                    sale_amount=sale_amount,
                )
            )

        # ---------------------------------------------------------
        # Technical Manager(s)
        # ---------------------------------------------------------

        eligible_manager_ids = (
            PhaseManagerHistory.objects
            .filter(
                phase__lead=lead,
                action=PhaseManagerHistory.Action.ACCEPTED,
            )
            .values_list("manager_id", flat=True)
            .distinct()
        )

        manager_rule = CommissionRule.objects.filter(
            role_name=Roles.TECHNICAL_MANAGER,
            is_active=True,
        ).first()

        if manager_rule and eligible_manager_ids:
            from apps.accounts.models import User

            managers = User.objects.filter(
                id__in=eligible_manager_ids
            )

            for manager in managers:
                records.append(
                    _build_record(
                        project=project,
                        user=manager,
                        rule=manager_rule,
                        sale_amount=sale_amount,
                    )
                )

        if records:
            CommissionRecord.objects.bulk_create(records)

    return records


def _build_record(project, user, rule, sale_amount):
    """
    Calculate and build one CommissionRecord.
    """

    commission_amount = (
        sale_amount
        * rule.commission_percentage
        / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    return CommissionRecord(
        project=project,
        user=user,
        role_name=rule.role_name,
        sale_amount=sale_amount,
        commission_percentage=rule.commission_percentage,
        commission_amount=commission_amount,
    )