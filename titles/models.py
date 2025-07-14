from django.db import models
import uuid
import re
class Genre(models.Model):
    name=models.CharField(max_length=50,unique=True,verbose_name="ジャンル名")
    description=models.TextField(blank=True,verbose_name="ジャンル説明")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="ジャンル"
        verbose_name_plural="ジャンル"
    def __str__(self):
        return self.name
class SubGenre(models.Model):
    name=models.CharField(max_length=50,unique=True,verbose_name="サブジャンル名")
    description=models.TextField(blank=True,verbose_name="サブジャンル説明")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="サブジャンル"
        verbose_name_plural="サブジャンル"
    def __str__(self):
        return self.name
class Tag(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=50,unique=True,verbose_name="タグ名")
    description=models.TextField(blank=True,verbose_name="タグ説明")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="タグ"
        verbose_name_plural="タグ"
    def __str__(self):
        return self.name

class Title(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    title=models.CharField(max_length=200,verbose_name="タイトル")
    title_kana=models.CharField(max_length=200,blank=True,verbose_name="タイトルふりがな")
    short_title=models.CharField(max_length=50,blank=True,verbose_name="タイトル略称")
    content=models.TextField(blank=True,verbose_name="概要")
    genre=models.ForeignKey(Genre,on_delete=models.PROTECT,verbose_name="ジャンル")
    sub_genre=models.ManyToManyField(SubGenre,blank=True,verbose_name="サブジャンル")
    season=models.PositiveIntegerField(verbose_name="シーズン")
    air_date=models.DateField(verbose_name="放送")
    website=models.URLField(blank=True,verbose_name="公式サイト")
    source_website=models.URLField(blank=True,verbose_name="ソース")
    related_titles=models.ManyToManyField("self",blank=True,verbose_name="関連タイトル")
    tags=models.ManyToManyField(Tag,blank=True,verbose_name="タグ")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    @property
    def content_without_url(self):
        text=re.sub(r'https?://[\w/:%#$&?()~.=+-]+', '', self.content)
        return ' '.join(text.split())
    class Meta:
        verbose_name="タイトル"
        verbose_name_plural="タイトル"
    def __str__(self):
        return self.title
class Episode(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    title=models.ForeignKey(Title,on_delete=models.CASCADE,related_name="episodes",verbose_name="タイトル")
    episode_title=models.CharField(max_length=200,blank=True,verbose_name="エピソードタイトル")
    episode_number=models.PositiveIntegerField(verbose_name="エピソード番号")
    content=models.TextField(blank=True,verbose_name="概要")
    air_date=models.DateTimeField(verbose_name="放送")
    duration=models.PositiveIntegerField(verbose_name="時間")
    website=models.URLField(blank=True,verbose_name="公式サイト")
    source_website=models.URLField(blank=True,verbose_name="ソース")
    tags=models.ManyToManyField(Tag,blank=True,verbose_name="タグ")
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="エピソード"
        verbose_name_plural="エピソード"
    def __str__(self):
        return self.title.title