from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
class UserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
    (None, {'fields': ('nickname', 'is_public')}),
)
    add_fieldsets = UserAdmin.add_fieldsets + (
    (None, {'fields': ('nickname', 'is_public')}),
)
admin.site.register(User,UserAdmin)