from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "CUSTOMER", "Customer"
        LOAN_OFFICER = "LOAN_OFFICER", "Loan Officer"

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    aadhaar_number = models.CharField(max_length=12, blank=True)


class LoanType(models.Model):
    name = models.CharField(max_length=80, unique=True)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=50000)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=5000000)
    base_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.50)
    max_duration_months = models.PositiveIntegerField(default=84)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class LoanApplication(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        DISBURSED = "DISBURSED", "Disbursed"
        CLOSED = "CLOSED", "Closed"

    class EmploymentType(models.TextChoices):
        SALARIED = "SALARIED", "Salaried"
        SELF_EMPLOYED = "SELF_EMPLOYED", "Self employed"
        STUDENT = "STUDENT", "Student"
        BUSINESS = "BUSINESS", "Business"
        UNEMPLOYED = "UNEMPLOYED", "Unemployed"

    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="loan_applications")
    loan_type = models.ForeignKey(LoanType, on_delete=models.PROTECT, related_name="applications")
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    pan_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(r"^[A-Z]{5}[0-9]{4}[A-Z]$", "Enter a valid PAN number.")],
    )
    aadhaar_number = models.CharField(
        max_length=12,
        validators=[RegexValidator(r"^[0-9]{12}$", "Enter a valid Aadhaar number.")],
    )
    address = models.TextField()
    salary = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices)
    existing_loans = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cibil_score = models.PositiveIntegerField(validators=[MinValueValidator(300), MaxValueValidator(900)])
    loan_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("10000"))])
    loan_duration_months = models.PositiveIntegerField(validators=[MinValueValidator(6), MaxValueValidator(360)])
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    prediction_label = models.CharField(max_length=20, blank=True)
    approval_probability = models.FloatField(default=0)
    risk_score = models.PositiveIntegerField(default=0)
    risk_level = models.CharField(max_length=20, blank=True)
    rejection_reason = models.TextField(blank=True)
    officer_remarks = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="reviewed_applications")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.loan_type.name}"


class Document(models.Model):
    class DocumentType(models.TextChoices):
        PAN = "PAN", "PAN Card"
        AADHAAR = "AADHAAR", "Aadhaar Card"
        SALARY_SLIP = "SALARY_SLIP", "Salary Slip"
        BANK_STATEMENT = "BANK_STATEMENT", "Bank Statement"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=20, choices=DocumentType.choices)
    file = models.FileField(
        upload_to="documents/%Y/%m/",
        validators=[FileExtensionValidator(["pdf", "png", "jpg", "jpeg"])],
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    remarks = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)


class EMIRecord(models.Model):
    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name="emi_schedule")
    due_date = models.DateField()
    principal_component = models.DecimalField(max_digits=12, decimal_places=2)
    interest_component = models.DecimalField(max_digits=12, decimal_places=2)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    class Meta:
        ordering = ["due_date"]


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name="payments")
    emi_record = models.ForeignKey(EMIRecord, null=True, blank=True, on_delete=models.SET_NULL, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_reference = models.CharField(max_length=120, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class CreditScore(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="credit_scores")
    score = models.PositiveIntegerField(validators=[MinValueValidator(300), MaxValueValidator(900)])
    source = models.CharField(max_length=80, default="Self reported")
    checked_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-checked_at"]


class Notification(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In app"
        EMAIL = "EMAIL", "Email"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=160)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
