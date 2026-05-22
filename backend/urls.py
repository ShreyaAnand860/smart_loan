from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from api import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.landing_page, name="landing"),
    path("register/", views.register_view, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/", views.SmartLoanPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"), name="password_reset_done"),
    path("password-reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(template_name="registration/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-reset/complete/", auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"), name="password_reset_complete"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("apply/", views.apply_loan_view, name="apply_loan"),
    path("loans/<int:pk>/", views.loan_detail_view, name="loan_detail"),
    path("loans/<int:pk>/review/", views.review_application_view, name="review_application"),
    path("documents/<int:pk>/verify/", views.verify_document_view, name="verify_document"),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
