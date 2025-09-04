from django.shortcuts import render, redirect
from django.views import View


class Profile(View):
    def get(self, request):
        return redirect("records:index")
