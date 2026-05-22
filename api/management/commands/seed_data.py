from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api.models import CreditScore
from api.services import seed_loan_types


class Command(BaseCommand):
    help = "Seed SmartLoan loan types and demo customer/officer users."

    def handle(self, *args, **options):
        seed_loan_types()
        User = get_user_model()
        demo_users = [
            ("customer", "customer@smartloan.local", User.Role.CUSTOMER, False),
            ("officer", "officer@smartloan.local", User.Role.LOAN_OFFICER, True),
        ]
        for username, email, role, is_staff in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email, "role": role, "is_staff": is_staff},
            )
            changed = False
            if user.role != role:
                user.role = role
                changed = True
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                changed = True
            if created:
                user.set_password("SmartLoan@123")
                changed = True
            if changed:
                user.save()
            if created and role == User.Role.CUSTOMER:
                CreditScore.objects.create(user=user, score=760, source="Demo")
        self.stdout.write(self.style.SUCCESS("SmartLoan seed data ready."))