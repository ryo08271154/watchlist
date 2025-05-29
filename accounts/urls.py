from django.urls import path
from . import views
from django.contrib.auth.views import LoginView,LogoutView
app_name="accounts"
urlpatterns=[path("login/",LoginView.as_view(),name="login"),
             path("logout/",LogoutView.as_view(),name="logout"),
             path("profile/",views.Profile.as_view(),name="profile")
             
]