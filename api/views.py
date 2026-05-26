from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import PasswordResetView
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST, require_http_methods
from rest_framework import permissions, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView


from ml_model.predictor import predict_loan

from .forms import (
    DocumentUploadForm,
    DocumentVerificationForm,
    LoanApplicationForm,
    LoanReviewForm,
    RegisterForm,
    SmartLoanPasswordResetForm,
)
from .models import (
    CreditScore,
    Document,
    EMIRecord,
    LoanApplication,
    LoanType,
    Notification,
    Payment,
    User,
)
from .serializers import (
    CreditScoreSerializer,
    DocumentSerializer,
    EMIRecordSerializer,
    LoanApplicationSerializer,
    LoanTypeSerializer,
    NotificationSerializer,
    PaymentSerializer,
    UserSerializer,
)
from .services import (
    create_emi_schedule,
    dashboard_metrics,
    emi_amount,
    notify,
    seed_loan_types,
    session_financial_tips,
)

FINALIZED_STATUSES = {LoanApplication.Status.APPROVED, LoanApplication.Status.REJECTED}


def is_loan_officer(user):
    return user.is_authenticated and user.role == User.Role.LOAN_OFFICER


def is_finalized(application):
    return application.status in FINALIZED_STATUSES


class SmartLoanPasswordResetView(PasswordResetView):
    template_name = "registration/password_reset.html"
    form_class = SmartLoanPasswordResetForm
    success_url = reverse_lazy("password_reset_done")
    email_template_name = "registration/password_reset_email.html"
    subject_template_name = "registration/password_reset_subject.txt"
    extra_email_context = {"product_name": "SmartLoan"}

    def _rate_key(self):
        email = self.request.POST.get("email", "").strip().lower()
        forwarded = self.request.META.get("HTTP_X_FORWARDED_FOR", "")
        ip = forwarded.split(",")[0].strip() or self.request.META.get(
            "REMOTE_ADDR", "unknown"
        )
        return f"password-reset:{ip}:{email}"

    def post(self, request, *args, **kwargs):
        key = self._rate_key()
        attempts = cache.get(key, 0)
        if attempts >= 5:
            form = self.get_form()
            form.add_error(
                None, "Too many reset attempts. Please try again in 15 minutes."
            )
            return self.form_invalid(form)
        cache.set(key, attempts + 1, 15 * 60)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(
            self.request,
            "If your account is active, a secure reset link has been sent.",
        )
        return super().form_valid(form)


def landing_page(request):
    seed_loan_types()
    return render(request, "landing.html", {"loan_types": LoanType.objects.all()})


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, "Welcome to SmartLoan. Your customer account is ready."
            )
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard_view(request):
    seed_loan_types()
    is_officer = request.user.role == User.Role.LOAN_OFFICER
    applications = LoanApplication.objects.select_related("loan_type", "applicant")
    if not is_officer:
        applications = applications.filter(applicant=request.user)
    notifications = request.user.notifications.all()[:8]
    context = {
        "is_officer_dashboard": is_officer,
        "metrics": dashboard_metrics(request.user),
        "applications": applications[: 25 if is_officer else 12],
        "notifications": notifications,
        "credit_scores": request.user.credit_scores.all()[:6],
        "status_counts": list(
            applications.values("status").annotate(count=Count("id"))
        ),
        "type_counts": list(
            applications.values("loan_type__name").annotate(count=Count("id"))
        ),
        "financial_tips": [] if is_officer else session_financial_tips(request),
    }
    return render(request, "dashboard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def apply_loan_view(request):
    if request.user.role == User.Role.LOAN_OFFICER:
        messages.warning(
            request, "Loan officers cannot submit customer loan applications."
        )
        return redirect("dashboard")
    seed_loan_types()
    if request.method == "POST":
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.applicant = request.user
            prediction = predict_loan(application)
            application.prediction_label = prediction["label"]
            application.approval_probability = prediction["probability"]
            application.risk_score = prediction["risk_score"]
            application.risk_level = prediction["risk_level"]
            application.rejection_reason = (
                "" if prediction["label"] == "Approved" else prediction["reason"]
            )
            application.status = LoanApplication.Status.UNDER_REVIEW
            application.save()
            CreditScore.objects.create(
                user=request.user,
                score=application.cibil_score,
                source="Loan application",
            )
            notify(
                request.user,
                "Application submitted",
                f"Your {application.loan_type.name} application is under review.",
                email=True,
            )
            messages.success(request, "Loan application submitted successfully.")
            messages.info(
                request, "Your application has been submitted and is under review."
            )
            return redirect("dashboard")
    else:
        form = LoanApplicationForm(
            initial={
                "full_name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
                "phone": request.user.phone,
                "pan_number": request.user.pan_number,
                "aadhaar_number": request.user.aadhaar_number,
                "address": request.user.address,
            }
        )
    return render(request, "apply_loan.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def loan_detail_view(request, pk):
    application = get_object_or_404(
        LoanApplication.objects.select_related("loan_type", "applicant", "reviewed_by"),
        pk=pk,
    )
    is_officer = request.user.role == User.Role.LOAN_OFFICER
    if not is_officer and application.applicant != request.user:
        return redirect("dashboard")
    if request.method == "POST" and not is_officer:

        # Prevent uploads after application finalization
        if is_finalized(application):

            messages.error(
                request, "Documents cannot be uploaded after application finalization."
            )

            return redirect("loan_detail", pk=pk)

        form = DocumentUploadForm(request.POST, request.FILES)

        if form.is_valid():

            document = form.save(commit=False)
            document.application = application
            document.save()

            messages.success(request, "Document uploaded for verification.")

            return redirect("loan_detail", pk=pk)

    else:
        form = DocumentUploadForm()
    monthly_emi = emi_amount(
        application.loan_amount,
        application.loan_type.base_interest_rate,
        application.loan_duration_months,
    )
    total_payment = monthly_emi * application.loan_duration_months
    context = {
        "application": application,
        "form": form,
        "is_officer_view": is_officer,
        "review_form": LoanReviewForm(initial={"decision": "APPROVED"}),
        "document_form": DocumentVerificationForm(),
        "emi_estimate": {
            "monthly": monthly_emi,
            "total": total_payment,
            "interest": total_payment - application.loan_amount,
        },
    }
    return render(request, "loan_detail.html", context)


@login_required
@user_passes_test(is_loan_officer)
@require_POST
def review_application_view(request, pk):
    form = LoanReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please correct the review form and try again.")
        return redirect("loan_detail", pk=pk)

    decision = form.cleaned_data["decision"]
    remarks = form.cleaned_data.get("officer_remarks", "")
    rejection_reason = form.cleaned_data.get("rejection_reason", "")

    with transaction.atomic():
        application = get_object_or_404(
            LoanApplication.objects.select_for_update().select_related("applicant"),
            pk=pk,
        )
        if is_finalized(application):
            messages.error(request, "This application has already been finalized.")
            return redirect("loan_detail", pk=pk)

        application.status = (
            LoanApplication.Status.APPROVED
            if decision == "APPROVED"
            else LoanApplication.Status.REJECTED
        )
        application.reviewed_by = request.user
        application.reviewed_at = timezone.now()
        application.officer_remarks = remarks
        application.rejection_reason = (
            "" if decision == "APPROVED" else rejection_reason
        )
        application.save(
            update_fields=[
                "status",
                "reviewed_by",
                "reviewed_at",
                "officer_remarks",
                "rejection_reason",
                "updated_at",
            ]
        )
        if decision == "APPROVED":
            create_emi_schedule(application)
            message = "Your loan application has been approved."
        else:
            message = (
                rejection_reason
                or "Your loan application was rejected due to eligibility criteria."
            )

    notify(
        application.applicant,
        f"Loan application {application.status.lower()}",
        message,
        email=True,
    )
    messages.success(
        request, f"Application {application.status.lower()} and customer notified."
    )
    return redirect("loan_detail", pk=pk)

@login_required
@user_passes_test(is_loan_officer)
@require_POST
def verify_document_view(request, pk):
    document = get_object_or_404(
        Document.objects.select_related("application"),
        pk=pk
    )

    if document.status in ["VERIFIED", "REJECTED"]:
        messages.error(
            request,
            "This document has already been finalized."
        )
        return redirect(
            "loan_detail",
            pk=document.application_id
        )

    form = DocumentVerificationForm(
        request.POST,
        instance=document
    )

    if form.is_valid():
        form.save()
        messages.success(
            request,
            "Document verification status updated."
        )
    else:
        messages.error(
            request,
            "Unable to update document verification status."
        )

    return redirect(
        "loan_detail",
        pk=document.application_id
    )


class IsLoanOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == User.Role.LOAN_OFFICER
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        if self.action in ["list", "destroy"]:
            return [IsLoanOfficer()]
        return [permissions.IsAuthenticated()]


class LoanTypeViewSet(viewsets.ModelViewSet):
    queryset = LoanType.objects.all()
    serializer_class = LoanTypeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class LoanApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = LoanApplicationSerializer
    filterset_fields = ["status", "loan_type"]

    def get_queryset(self):
        if self.request.user.role == User.Role.CUSTOMER:
            return LoanApplication.objects.filter(applicant=self.request.user)
        return LoanApplication.objects.all()

    def perform_create(self, serializer):
        application = serializer.save(
            applicant=self.request.user, status=LoanApplication.Status.UNDER_REVIEW
        )
        prediction = predict_loan(application)
        application.prediction_label = prediction["label"]
        application.approval_probability = prediction["probability"]
        application.risk_score = prediction["risk_score"]
        application.risk_level = prediction["risk_level"]
        application.rejection_reason = (
            "" if prediction["label"] == "Approved" else prediction["reason"]
        )
        application.save(
            update_fields=[
                "prediction_label",
                "approval_probability",
                "risk_score",
                "risk_level",
                "rejection_reason",
            ]
        )
        notify(
            self.request.user,
            "Application submitted",
            f"{application.loan_type.name} application submitted.",
            email=True,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsLoanOfficer])
    def review(self, request, pk=None):
        decision = request.data.get("decision")
        remarks = request.data.get("remarks", "")
        rejection_reason = request.data.get("rejection_reason", "")
        if decision not in ["APPROVED", "REJECTED"]:
            return Response(
                {"detail": "decision must be APPROVED or REJECTED"}, status=400
            )
        if decision == "REJECTED" and not rejection_reason:
            return Response(
                {
                    "detail": "rejection_reason is required when rejecting an application"
                },
                status=400,
            )

        with transaction.atomic():
            application = get_object_or_404(
                LoanApplication.objects.select_for_update().select_related("applicant"),
                pk=pk,
            )
            if is_finalized(application):
                return Response(
                    {"detail": "This application has already been finalized."},
                    status=400,
                )

            application.status = decision
            application.officer_remarks = remarks
            application.rejection_reason = (
                "" if decision == "APPROVED" else rejection_reason
            )
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            application.save(
                update_fields=[
                    "status",
                    "officer_remarks",
                    "rejection_reason",
                    "reviewed_by",
                    "reviewed_at",
                    "updated_at",
                ]
            )
            if decision == "APPROVED":
                create_emi_schedule(application)
                message = "Your loan application has been approved."
            else:
                message = rejection_reason

        notify(
            application.applicant,
            f"Loan application {decision.lower()}",
            message,
            email=True,
        )
        return Response(self.get_serializer(application).data)

    @action(detail=True, methods=["get"])
    def predict(self, request, pk=None):
        return Response(predict_loan(self.get_object()))


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    filterset_fields = ["status", "document_type"]

    def get_queryset(self):
        qs = Document.objects.select_related("application", "application__applicant")
        if self.request.user.role == User.Role.CUSTOMER:
            qs = qs.filter(application__applicant=self.request.user)
        return qs


class EMIRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = EMIRecordSerializer

    def get_queryset(self):
        qs = EMIRecord.objects.select_related("application")
        if self.request.user.role == User.Role.CUSTOMER:
            qs = qs.filter(application__applicant=self.request.user)
        return qs


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.select_related("application")
        if self.request.user.role == User.Role.CUSTOMER:
            qs = qs.filter(application__applicant=self.request.user)
        return qs


class CreditScoreViewSet(viewsets.ModelViewSet):
    serializer_class = CreditScoreSerializer

    def get_queryset(self):
        return CreditScore.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def dashboard_api(request):
    return Response(dashboard_metrics(request.user))


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def emi_calculator_api(request):
    principal = float(request.data.get("principal", 0))
    rate = float(request.data.get("interest_rate", 0))
    months = int(request.data.get("time", 1))
    monthly_rate = rate / 1200
    emi = (
        principal / months
        if monthly_rate == 0
        else principal
        * monthly_rate
        * ((1 + monthly_rate) ** months)
        / (((1 + monthly_rate) ** months) - 1)
    )
    total = emi * months
    return Response(
        {
            "monthly_emi": round(emi, 2),
            "total_payment": round(total, 2),
            "interest_amount": round(total - principal, 2),
        }
    )


class SmartLoanTokenView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
