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

        widgets = {
            "phone": forms.TextInput(
                attrs={
                    "maxlength": "10",
                    "pattern": "[0-9]{10}",
                    "inputmode": "numeric",
                    "placeholder": "Enter 10-digit mobile number",
                }
            ),

            "cibil_score": forms.NumberInput(
                attrs={
                    "min": "300",
                    "max": "900",
                    "maxlength": "3",
                }
            ),

            "loan_duration_months": forms.NumberInput(
                attrs={
                    "min": "6",
                    "max": "360",
                    "maxlength": "3",
                }
            ),
        }

    def clean_phone(self):
        phone = str(self.cleaned_data.get("phone", "")).strip()

        if not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")

        if len(phone) != 10:
            raise forms.ValidationError("Phone number must be exactly 10 digits.")

        return phone

    def clean_cibil_score(self):
        score = self.cleaned_data.get("cibil_score")

        if score is None:
            return score

        if score < 300 or score > 900:
            raise forms.ValidationError(
                "CIBIL score must be between 300 and 900."
            )

        return score

    def clean_loan_duration_months(self):
        tenure = self.cleaned_data.get("loan_duration_months")

        if tenure is None:
            return tenure

        if tenure < 6 or tenure > 360:
            raise forms.ValidationError(
                "Loan tenure must be between 6 and 360 months."
            )

        return tenure


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
