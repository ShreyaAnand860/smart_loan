from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="users")
router.register("loan-types", views.LoanTypeViewSet)
router.register("loan-applications", views.LoanApplicationViewSet, basename="loan-applications")
router.register("documents", views.DocumentViewSet, basename="documents")
router.register("emi-records", views.EMIRecordViewSet, basename="emi-records")
router.register("payments", views.PaymentViewSet, basename="payments")
router.register("credit-scores", views.CreditScoreViewSet, basename="credit-scores")
router.register("notifications", views.NotificationViewSet, basename="notifications")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/token/", views.SmartLoanTokenView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("dashboard/", views.dashboard_api, name="dashboard_api"),
    path("emi-calculator/", views.emi_calculator_api, name="emi_calculator_api"),
]
