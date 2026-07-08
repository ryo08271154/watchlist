from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.conf import settings
from django.contrib.auth import login

from accounts.forms import SignUpForm, UserForm
from accounts.models import User


class ProfileView(TemplateView):
    template_name = "registration/profile.html"


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    template_name = "form.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self):
        return self.request.user


class SetupView(View):
    def get(self, request):
        is_authenticated = request.user.is_authenticated

        if is_authenticated:
            user = request.user
            user_info = {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        else:
            user_info = None

        return JsonResponse({
            "name": "視聴記録",
            "v": 1,
            "is_login": is_authenticated,
            "user": user_info,
        })


class SignupView(CreateView):
    form_class = SignUpForm
    template_name = "registration/login.html"
    success_url = reverse_lazy("records:index")

    def dispatch(self, request, *args, **kwargs):
        if not settings.ALLOW_SIGNUP:
            raise Http404()

        if request.user.is_authenticated:
            return redirect("records:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mode"] = "signup"
        return context
