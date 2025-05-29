from django.forms import ModelForm
from django import forms
from .models import WatchRecord,EpisodeWatchRecord,MyList
class ReviewForm(ModelForm):
    class Meta:
        model=WatchRecord
        fields=["comment_title","comment","watched_date","rating","status","watch_method","tags"]
class EpisodeReviewForm(ModelForm):
    class Meta:
        model=EpisodeWatchRecord
        fields=["comment_title","comment","watched_date","rating","status","watch_method","tags"]
class MyListForm(ModelForm):
    class Meta:
        model=MyList
        fields=["name","description","titles","tags","is_public"]
class ReviewFileImportForm(forms.Form):
    file=forms.FileField(label="ファイル",allow_empty_file=True)
    start_row=forms.IntegerField(label="開始行",min_value=1)
    title_column=forms.IntegerField(label="タイトル列",min_value=1)
    genre_column=forms.IntegerField(label="ジャンル列",min_value=1)
    air_date_column=forms.IntegerField(label="放送列",min_value=1)
    season_column=forms.IntegerField(label="シーズン列",min_value=1)
    comment_title_column=forms.IntegerField(label="コメントタイトル列",min_value=1)
    comment_column=forms.IntegerField(label="コメント列",min_value=1)
    watched_date_column=forms.IntegerField(label="視聴日列",min_value=1)
    rating_column=forms.IntegerField(label="評価列",min_value=1)
    status_column=forms.IntegerField(label="視聴状況列",min_value=1)
    watch_method_column=forms.IntegerField(label="視聴方法列",min_value=1)