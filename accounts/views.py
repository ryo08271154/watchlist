from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View


class Profile(View):
    def get(self, request):
        return redirect("records:index")


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
