from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    # Built-in class-based auth views, we only supply templates and context.
    path("login/", auth_views.LoginView.as_view(
        template_name="accounts/login.html", redirect_authenticated_user=True), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),  # POST only in Django 5
    path("settings/", views.profile_edit, name="settings"),
    path("activity/", views.my_activity, name="activity"),
    path("password/", auth_views.PasswordChangeView.as_view(
        template_name="accounts/form.html",
        success_url=reverse_lazy("accounts:password_done"),
        extra_context={"title": "Change password", "submit_label": "Update password"}),
        name="password_change"),
    path("password/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/message.html",
        extra_context={"title": "Password changed", "text": "Your password was updated."}),
        name="password_done"),
    # Forgot-password flow (e-mails are printed in the console during development)
    path("reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/form.html",
        email_template_name="accounts/password_reset_email.txt",
        success_url=reverse_lazy("accounts:reset_sent"),
        extra_context={"title": "Reset your password", "submit_label": "Send reset link"}),
        name="password_reset"),
    path("reset/sent/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/message.html",
        extra_context={"title": "Check your e-mail", "text": "If that address has an account, a reset link is on its way."}),
        name="reset_sent"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/form.html",
        success_url=reverse_lazy("accounts:reset_complete"),
        extra_context={"title": "Choose a new password", "submit_label": "Save password"}),
        name="password_reset_confirm"),
    path("reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/message.html",
        extra_context={"title": "All set", "text": "Your password has been reset. You can log in now.",
                       "link": ("Log in", "accounts:login")}),
        name="reset_complete"),
    # <str:username> is a URL parameter (Unit II). Keep it last so it never hides the paths above.
    path("u/<str:username>/", views.profile, name="profile"),
]
