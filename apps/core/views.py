from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q, Sum
from django.shortcuts import render

from apps.accounts.permissions import (
    is_business_developer,
    is_engineer,
    is_super_admin,
    is_technical_manager,
)
from apps.commissions.models import CommissionRecord
from apps.leads.choices import LeadStatus, PhaseStatus
from apps.leads.models import Lead, Phase, PhaseEngineer
from apps.projects.models import Project


@login_required
def dashboard_page(request):
    user = request.user
    super_admin = is_super_admin(user)
    bd = is_business_developer(user) or super_admin
    tm = is_technical_manager(user)
    engineer = is_engineer(user)

    open_leads = Lead.objects.filter(status=LeadStatus.OPEN).count()
    sale_leads = Lead.objects.filter(status=LeadStatus.SALE).count()
    no_sale_leads = Lead.objects.filter(status=LeadStatus.NO_SALE).count()
    active_projects = Project.objects.filter(status="active").count()

    commissions = CommissionRecord.objects.filter(user=user)
    commission_total = commissions.aggregate(total=Sum("commission_amount"))["total"] or 0
    total_commission_org = CommissionRecord.objects.aggregate(total=Sum("commission_amount"))["total"] or 0
    total_leads = Lead.objects.count()

    ready_to_decide = Lead.objects.none()
    needs_reassignment = Phase.objects.none()
    pending_phases = Phase.objects.none()
    pending_engineer = PhaseEngineer.objects.none()
    active_engineer = PhaseEngineer.objects.none()

    if bd:
        ready_to_decide = (
            Lead.objects.filter(status=LeadStatus.OPEN)
            .annotate(
                phase_count=Count("phases"),
                completed_count=Count(
                    "phases",
                    filter=Q(phases__status=PhaseStatus.COMPLETED),
                ),
            )
            .filter(phase_count__gt=0, phase_count=F("completed_count"))
            .select_related("created_by")
            .order_by("-updated_at")
        )
        needs_reassignment = (
            Phase.objects.filter(status=PhaseStatus.PENDING_REASSIGNMENT)
            .select_related("lead")
            .order_by("due_date")
        )

    if tm:
        pending_phases = (
            Phase.objects.filter(
                current_manager=user,
                status=PhaseStatus.PENDING_ACCEPTANCE,
            )
            .select_related("lead")
            .order_by("due_date")
        )
    elif super_admin:
        pending_phases = (
            Phase.objects.filter(status=PhaseStatus.PENDING_ACCEPTANCE)
            .select_related("lead", "current_manager")
            .order_by("due_date")
        )

    if engineer:
        pending_engineer = (
            PhaseEngineer.objects.filter(
                engineer=user,
                status=PhaseEngineer.Status.PENDING,
            )
            .select_related("phase__lead")
            .order_by("phase__due_date")
        )
        active_engineer = (
            PhaseEngineer.objects.filter(
                engineer=user,
                status=PhaseEngineer.Status.ACCEPTED,
            )
            .select_related("phase__lead")
            .order_by("phase__due_date")
        )

    role_guides = []
    if super_admin:
        role_guides.append(
            {
                "role": "Super Admin",
                "text": "Oversee the pipeline, assign user roles, and step into any workflow.",
            }
        )
    if is_business_developer(user):
        role_guides.append(
            {
                "role": "Business Developer",
                "text": "Create leads, add phases, assign technical managers, and close sales.",
            }
        )
    if tm:
        role_guides.append(
            {
                "role": "Technical Manager",
                "text": "Accept assigned phases, add engineers, and mark phases complete.",
            }
        )
    if engineer:
        role_guides.append(
            {
                "role": "Engineer",
                "text": "Accept assigned work, complete it, and mark it done.",
            }
        )

    return render(
        request,
        "dashboard.html",
        {
            "total_leads": total_leads,
            "open_leads": open_leads,
            "sale_leads": sale_leads,
            "no_sale_leads": no_sale_leads,
            "active_projects": active_projects,
            "commission_total": commission_total,
            "commission_count": commissions.count(),
            "total_commission_org": total_commission_org,
            "ready_to_decide": ready_to_decide[:8],
            "ready_to_decide_count": ready_to_decide.count() if bd else 0,
            "needs_reassignment": needs_reassignment[:8],
            "pending_phases": pending_phases[:8],
            "pending_engineer": pending_engineer[:8],
            "active_engineer": active_engineer[:8],
            "recent_leads": Lead.objects.select_related("created_by").order_by("-created_at")[:8],
            "show_bd_queue": bd,
            "show_tm_queue": tm or super_admin,
            "show_engineer_queue": engineer,
            "show_commissions": bd or tm or super_admin,
            "role_guides": role_guides,
            "user_count": user_role_counts() if super_admin else None,
        },
    )


def user_role_counts():
    from apps.accounts.models import User
    from apps.accounts.roles import Roles

    return {
        "total": User.objects.filter(is_active=True).count(),
        "super_admin": User.objects.filter(
            Q(groups__name=Roles.SUPER_ADMIN) | Q(is_superuser=True),
            is_active=True,
        ).distinct().count(),
        "business_developer": User.objects.filter(groups__name=Roles.BUSINESS_DEVELOPER, is_active=True).count(),
        "technical_manager": User.objects.filter(groups__name=Roles.TECHNICAL_MANAGER, is_active=True).count(),
        "engineer": User.objects.filter(groups__name=Roles.ENGINEER, is_active=True).count(),
    }

