from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    nickname=models.CharField(max_length=100,blank=True,verbose_name="ニックネーム")
    is_public=models.BooleanField(default=False,verbose_name="公開")