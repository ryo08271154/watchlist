from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
app_name = "accounts"
urlpatterns = [path("login/", LoginView.as_view(), name="login"),
               path("logout/", LogoutView.as_view(), name="logout"),
               path("profile/", views.ProfileView.as_view(), name="profile"),
               path("profile/edit/", views.ProfileEditView.as_view(),
                    name="profile_edit"),
               path("setup/", views.SetupView.as_view(), name="setup"),
               path("signup/", views.SignupView.as_view(), name="signup"),
               path("password_change/", PasswordChangeView.as_view(template_name="form.html", extra_context={
                    "mode": "password_change"}, success_url=reverse_lazy("records:index"), ), name="password_change"),
               ]
