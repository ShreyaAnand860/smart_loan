# Generated for SmartLoan initial schema.
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("username", models.CharField(error_messages={"unique": "A user with that username already exists."}, help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.", max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name="username")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("role", models.CharField(choices=[("CUSTOMER", "Customer"), ("OFFICER", "Loan Officer"), ("ADMIN", "Admin")], default="CUSTOMER", max_length=20)),
                ("phone", models.CharField(blank=True, max_length=15)),
                ("address", models.TextField(blank=True)),
                ("pan_number", models.CharField(blank=True, max_length=10)),
                ("aadhaar_number", models.CharField(blank=True, max_length=12)),
                ("groups", models.ManyToManyField(blank=True, help_text="The groups this user belongs to.", related_name="user_set", related_query_name="user", to="auth.group", verbose_name="groups")),
                ("user_permissions", models.ManyToManyField(blank=True, help_text="Specific permissions for this user.", related_name="user_set", related_query_name="user", to="auth.permission", verbose_name="user permissions")),
            ],
            options={"verbose_name": "user", "verbose_name_plural": "users", "abstract": False},
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
        migrations.CreateModel(
            name="LoanType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("min_amount", models.DecimalField(decimal_places=2, default=50000, max_digits=12)),
                ("max_amount", models.DecimalField(decimal_places=2, default=5000000, max_digits=12)),
                ("base_interest_rate", models.DecimalField(decimal_places=2, default=10.5, max_digits=5)),
                ("max_duration_months", models.PositiveIntegerField(default=84)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="LoanApplication",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=150)),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(max_length=15)),
                ("pan_number", models.CharField(max_length=10, validators=[django.core.validators.RegexValidator("^[A-Z]{5}[0-9]{4}[A-Z]$", "Enter a valid PAN number.")])),
                ("aadhaar_number", models.CharField(max_length=12, validators=[django.core.validators.RegexValidator("^[0-9]{12}$", "Enter a valid Aadhaar number.")])),
                ("address", models.TextField()),
                ("salary", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ("employment_type", models.CharField(choices=[("SALARIED", "Salaried"), ("SELF_EMPLOYED", "Self employed"), ("STUDENT", "Student"), ("BUSINESS", "Business"), ("UNEMPLOYED", "Unemployed")], max_length=20)),
                ("existing_loans", models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ("cibil_score", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(300), django.core.validators.MaxValueValidator(900)])),
                ("loan_amount", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(10000)])),
                ("loan_duration_months", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(6), django.core.validators.MaxValueValidator(360)])),
                ("purpose", models.TextField()),
                ("status", models.CharField(choices=[("DRAFT", "Draft"), ("SUBMITTED", "Submitted"), ("UNDER_REVIEW", "Under Review"), ("APPROVED", "Approved"), ("REJECTED", "Rejected"), ("DISBURSED", "Disbursed"), ("CLOSED", "Closed")], default="SUBMITTED", max_length=20)),
                ("prediction_label", models.CharField(blank=True, max_length=20)),
                ("approval_probability", models.FloatField(default=0)),
                ("risk_score", models.PositiveIntegerField(default=0)),
                ("risk_level", models.CharField(blank=True, max_length=20)),
                ("rejection_reason", models.TextField(blank=True)),
                ("officer_remarks", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("applicant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="loan_applications", to=settings.AUTH_USER_MODEL)),
                ("loan_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="applications", to="api.loantype")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_applications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="CreditScore",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(300), django.core.validators.MaxValueValidator(900)])),
                ("source", models.CharField(default="Self reported", max_length=80)),
                ("checked_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="credit_scores", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-checked_at"]},
        ),
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("document_type", models.CharField(choices=[("PAN", "PAN Card"), ("AADHAAR", "Aadhaar Card"), ("SALARY_SLIP", "Salary Slip"), ("BANK_STATEMENT", "Bank Statement")], max_length=20)),
                ("file", models.FileField(upload_to="documents/%Y/%m/", validators=[django.core.validators.FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])])),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("VERIFIED", "Verified"), ("REJECTED", "Rejected")], default="PENDING", max_length=20)),
                ("remarks", models.TextField(blank=True)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="documents", to="api.loanapplication")),
            ],
        ),
        migrations.CreateModel(
            name="EMIRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("due_date", models.DateField()),
                ("principal_component", models.DecimalField(decimal_places=2, max_digits=12)),
                ("interest_component", models.DecimalField(decimal_places=2, max_digits=12)),
                ("amount_due", models.DecimalField(decimal_places=2, max_digits=12)),
                ("is_paid", models.BooleanField(default=False)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="emi_schedule", to="api.loanapplication")),
            ],
            options={"ordering": ["due_date"]},
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=160)),
                ("message", models.TextField()),
                ("channel", models.CharField(choices=[("IN_APP", "In app"), ("EMAIL", "Email")], default="IN_APP", max_length=20)),
                ("is_read", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="notifications", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Payment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("transaction_reference", models.CharField(blank=True, max_length=120)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="payments", to="api.loanapplication")),
                ("emi_record", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="payments", to="api.emirecord")),
            ],
        ),
    ]
