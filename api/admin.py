import csv

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.http import HttpResponse

from .models import CreditScore, Document, EMIRecord, LoanApplication, LoanType, Notification, Payment, User


def export_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{modeladmin.model._meta.model_name}.csv"'
    writer = csv.writer(response)
    fields = [field.name for field in modeladmin.model._meta.fields]
    writer.writerow(fields)
    for obj in queryset:
        writer.writerow([getattr(obj, field) for field in fields])
    return response


export_csv.short_description = "Export selected rows as CSV"


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ["username", "email", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "is_staff"]
    search_fields = ["username", "email", "phone", "pan_number"]
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("SmartLoan profile", {"fields": ("role", "phone", "address", "pan_number", "aadhaar_number")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("SmartLoan profile", {"fields": ("role", "phone", "address", "pan_number", "aadhaar_number")}),
    )
    actions = [export_csv]


@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "base_interest_rate", "min_amount", "max_amount", "max_duration_months"]
    search_fields = ["name"]


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0


class EMIInline(admin.TabularInline):
    model = EMIRecord
    extra = 0
    readonly_fields = ["due_date", "principal_component", "interest_component", "amount_due", "is_paid"]


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ["full_name", "loan_type", "loan_amount", "status", "approval_probability", "risk_level", "reviewed_by", "reviewed_at", "created_at"]
    list_filter = ["status", "loan_type", "employment_type", "risk_level"]
    search_fields = ["full_name", "email", "phone", "pan_number"]
    readonly_fields = ["prediction_label", "approval_probability", "risk_score", "risk_level", "reviewed_at"]
    inlines = [DocumentInline, EMIInline]
    actions = [export_csv]


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ["application", "document_type", "status", "uploaded_at"]
    list_filter = ["document_type", "status"]
    actions = [export_csv]


@admin.register(EMIRecord)
class EMIRecordAdmin(admin.ModelAdmin):
    list_display = ["application", "due_date", "amount_due", "is_paid"]
    list_filter = ["is_paid", "due_date"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["application", "amount", "status", "transaction_reference", "created_at"]
    list_filter = ["status", "created_at"]


@admin.register(CreditScore)
class CreditScoreAdmin(admin.ModelAdmin):
    list_display = ["user", "score", "source", "checked_at"]
    list_filter = ["source", "checked_at"]


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "title", "channel", "is_read", "created_at"]
    list_filter = ["channel", "is_read"]
