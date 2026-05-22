from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm

from .models import Document, LoanApplication, User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "phone", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CUSTOMER
        if commit:
            user.save()
        return user


class SmartLoanPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Email address",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
                "class": "form-control",
                "placeholder": "you@example.com",
            }
        ),
        error_messages={
            "required": "Please enter your email address.",
            "invalid": "Enter a valid email address.",
        },
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if not User.objects.filter(email__iexact=email, is_active=True).exists():
            raise forms.ValidationError("No account found with this email address.")
        return email


class LoanApplicationForm(forms.ModelForm):
    class Meta:
        model = LoanApplication
        exclude = [
            "applicant",
            "status",
            "prediction_label",
            "approval_probability",
            "risk_score",
            "risk_level",
            "rejection_reason",
            "officer_remarks",
            "reviewed_by",
            "reviewed_at",
        ]


class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["document_type", "file"]


class LoanReviewForm(forms.ModelForm):
    decision = forms.ChoiceField(
        choices=[("APPROVED", "Approve"), ("REJECTED", "Reject")],
        widget=forms.RadioSelect,
    )

    class Meta:
        model = LoanApplication
        fields = ["decision", "officer_remarks", "rejection_reason"]
        widgets = {
            "officer_remarks": forms.Textarea(attrs={"rows": 4, "placeholder": "Add review notes for the customer and audit trail."}),
            "rejection_reason": forms.Textarea(attrs={"rows": 3, "placeholder": "Required when rejecting an application."}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("decision") == "REJECTED" and not cleaned.get("rejection_reason"):
            self.add_error("rejection_reason", "Please provide a rejection reason.")
        return cleaned


class DocumentVerificationForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ["status", "remarks"]
        widgets = {
            "remarks": forms.Textarea(attrs={"rows": 2, "placeholder": "Optional verification remarks."}),
        }