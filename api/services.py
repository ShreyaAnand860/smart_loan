from datetime import timedelta
from decimal import Decimal
from random import sample

from django.core.mail import send_mail
from django.db.models import Count, Sum
from django.utils import timezone

from .models import EMIRecord, LoanApplication, LoanType, Notification

FINANCIAL_TIPS = [
    {
        "title": "Protect your approval odds",
        "body": "Keep total EMIs below 40 percent of monthly income before applying for a new loan.",
    },
    {
        "title": "Use shorter tenure carefully",
        "body": "A shorter tenure can reduce total interest, but only choose an EMI that leaves enough monthly buffer.",
    },
    {
        "title": "Strengthen your credit profile",
        "body": "Pay credit card bills before the due date and keep utilization below 30 percent.",
    },
    {
        "title": "Compare total cost",
        "body": "Review processing fees, insurance, prepayment charges, and interest before choosing a product.",
    },
    {
        "title": "Avoid duplicate applications",
        "body": "Multiple hard enquiries in a short period can temporarily reduce your credit score.",
    },
    {
        "title": "Keep documents consistent",
        "body": "Use the same name, PAN, address, and phone number across application and uploaded documents.",
    },
    {
        "title": "Build an emergency buffer",
        "body": "Keep at least three months of EMIs available before taking a high-value loan.",
    },
    {
        "title": "Prepay high-interest debt first",
        "body": "Clearing expensive unsecured debt can improve eligibility and reduce total interest outflow.",
    },
]


def seed_loan_types():
    defaults = [
        ("Personal Loan", 50000, 2500000, 11.5, 84),
        ("Home Loan", 500000, 20000000, 8.75, 360),
        ("Education Loan", 50000, 7500000, 9.25, 180),
        ("Business Loan", 100000, 10000000, 13.0, 120),
        ("Vehicle Loan", 50000, 3000000, 9.8, 96),
    ]
    for name, min_amount, max_amount, rate, months in defaults:
        LoanType.objects.get_or_create(
            name=name,
            defaults={
                "min_amount": min_amount,
                "max_amount": max_amount,
                "base_interest_rate": rate,
                "max_duration_months": months,
                "description": f"SmartLoan {name.lower()} with AI-assisted eligibility checks.",
            },
        )


def emi_amount(principal, annual_rate, months):
    principal = Decimal(principal)
    monthly_rate = Decimal(annual_rate) / Decimal(1200)
    if monthly_rate == 0:
        return principal / Decimal(months)
    factor = (1 + monthly_rate) ** months
    return principal * monthly_rate * factor / (factor - 1)


def create_emi_schedule(application):
    if application.emi_schedule.exists():
        return
    rate = application.loan_type.base_interest_rate
    emi = emi_amount(application.loan_amount, rate, application.loan_duration_months)
    remaining = Decimal(application.loan_amount)
    monthly_rate = Decimal(rate) / Decimal(1200)
    start = timezone.localdate().replace(day=1) + timedelta(days=32)
    due = start.replace(day=5)
    rows = []
    for index in range(application.loan_duration_months):
        interest = remaining * monthly_rate
        principal = emi - interest
        remaining = max(Decimal("0"), remaining - principal)
        rows.append(
            EMIRecord(
                application=application,
                due_date=due + timedelta(days=30 * index),
                principal_component=principal.quantize(Decimal("0.01")),
                interest_component=interest.quantize(Decimal("0.01")),
                amount_due=emi.quantize(Decimal("0.01")),
            )
        )
    EMIRecord.objects.bulk_create(rows)


def notify(user, title, message, email=False):
    Notification.objects.create(user=user, title=title, message=message, channel="EMAIL" if email else "IN_APP")
    if email and user.email:
        send_mail(title, message, None, [user.email], fail_silently=True)


def session_financial_tips(request, count=3):
    tips = sample(FINANCIAL_TIPS, k=min(count, len(FINANCIAL_TIPS)))
    request.session["financial_tips"] = tips
    request.session.modified = True
    return tips


def dashboard_metrics(user):
    qs = LoanApplication.objects.all()
    if user.role == "CUSTOMER":
        qs = qs.filter(applicant=user)
    return {
        "total": qs.count(),
        "approved": qs.filter(status=LoanApplication.Status.APPROVED).count(),
        "rejected": qs.filter(status=LoanApplication.Status.REJECTED).count(),
        "requested_amount": qs.aggregate(total=Sum("loan_amount"))["total"] or 0,
        "by_status": list(qs.values("status").annotate(count=Count("id")).order_by("status")),
        "by_type": list(qs.values("loan_type__name").annotate(count=Count("id")).order_by("loan_type__name")),
    }
