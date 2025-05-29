from django.db import models
from django.conf import settings
import uuid
from django.core.validators import MaxValueValidator, MinValueValidator
from titles.models import Title,Tag,Episode
class WatchMethod(models.Model):
    name=models.CharField(max_length=50,unique=True,verbose_name="視聴方法")
    description=models.TextField(blank=True,verbose_name="視聴方法説明")
    website=models.URLField(blank=True,verbose_name="公式サイト")
    search_url=models.URLField(blank=True,verbose_name="検索URL")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="視聴方法"
        verbose_name_plural="視聴方法"
    def __str__(self):
        return self.name

WATCH_STATUS_CHOICES = [
    ('watched', '視聴済み'),
    ('watching', '視聴中'),
    ('not_watched', '未視聴'),
    ('dropped', '視聴中断'),
]
class WatchRecord(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,verbose_name="ユーザー",editable=False)
    title=models.ForeignKey(Title,on_delete=models.PROTECT,verbose_name="タイトル")
    comment_title=models.CharField(max_length=200,verbose_name="コメントタイトル",blank=True)
    comment=models.TextField(blank=True,verbose_name="コメント")
    watched_date=models.DateField(blank=True,null=True,verbose_name="視聴日")
    rating=models.PositiveIntegerField(blank=True,null=True,validators=[MinValueValidator(1),MaxValueValidator(100)],verbose_name="評価")
    is_spoiler=models.BooleanField(default=False,verbose_name="ネタバレ")
    status=models.CharField(choices=WATCH_STATUS_CHOICES,max_length=20,blank=True,verbose_name="視聴状況")
    watch_method=models.ForeignKey(WatchMethod,on_delete=models.PROTECT,blank=True,null=True,verbose_name="視聴方法")
    tags=models.ManyToManyField(Tag,blank=True,verbose_name="タグ")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="視聴記録"
        verbose_name_plural="視聴記録"
    def __str__(self):
        return self.title.title
class EpisodeWatchRecord(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,verbose_name="ユーザー",editable=False)
    episode=models.ForeignKey(Episode,on_delete=models.PROTECT,verbose_name="エピソード")
    comment_title=models.CharField(max_length=200,verbose_name="コメントタイトル",blank=True)
    comment=models.TextField(blank=True,verbose_name="コメント")
    watched_date=models.DateField(blank=True,null=True,verbose_name="視聴日")
    rating=models.PositiveIntegerField(blank=True,null=True,validators=[MinValueValidator(1),MaxValueValidator(100)],verbose_name="評価")
    is_spoiler=models.BooleanField(default=False,verbose_name="ネタバレ")
    status=models.CharField(choices=WATCH_STATUS_CHOICES,max_length=20,blank=True,verbose_name="視聴状況")
    watch_method=models.ForeignKey(WatchMethod,on_delete=models.PROTECT,blank=True,null=True,verbose_name="視聴方法")
    tags=models.ManyToManyField(Tag,blank=True,verbose_name="タグ")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="エピソード視聴記録"
        verbose_name_plural="エピソード視聴記録"
    def __str__(self):
        return self.episode.title.title
class MyList(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,verbose_name="ユーザー",editable=False)
    name=models.CharField(max_length=200,verbose_name="リスト名")
    description=models.TextField(blank=True,verbose_name="リスト説明")
    titles=models.ManyToManyField(Title,blank=True,verbose_name="タイトル")
    tags=models.ManyToManyField(Tag,blank=True,verbose_name="タグ")
    is_public=models.BooleanField(default=False,verbose_name="公開")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="マイリスト"
        verbose_name_plural="マイリスト"
    def __str__(self):
        return self.name