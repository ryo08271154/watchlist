from django.forms import ModelForm
from .models import Title,Episode,Tag
from django import forms
class TitleForm(ModelForm):
    class Meta:
        model=Title
        fields=["title","title_kana","short_title","content","genre","sub_genre","season","air_date","website","related_titles","tags"]
class EpisodeForm(ModelForm):
    class Meta:
        model=Episode
        fields=["episode_title","episode_number","content","air_date","duration","tags",]
class TagForm(ModelForm):
    class Meta:
        model=Tag
        fields="__all__"
class TitleFileImportForm(forms.Form):
    file=forms.FileField(label="ファイル")
    start_row=forms.IntegerField(label="開始行",min_value=1)
    title_column=forms.IntegerField(label="タイトル列",min_value=1)
    title_kana_column=forms.IntegerField(label="タイトルふりがな列",min_value=1)
    short_title_column=forms.IntegerField(label="タイトル略称列",min_value=1)
    content_column=forms.IntegerField(label="概要列",min_value=1)
    genre_column=forms.IntegerField(label="ジャンル列",min_value=1)
    sub_genre_column=forms.IntegerField(label="サブジャンル列",min_value=1)
    season_column=forms.IntegerField(label="シーズン列",min_value=1)
    air_date_column=forms.IntegerField(label="放送列",min_value=1)
    website_column=forms.IntegerField(label="公式サイト列",min_value=1)
class EpisodeFileImportForm(forms.Form):
    file=forms.FileField(label="ファイル")
    start_row=forms.IntegerField(label="開始行",min_value=1)
    episode_title_column=forms.IntegerField(label="エピソードタイトル列",min_value=1)
    episode_number_column=forms.IntegerField(label="エピソード番号列",min_value=1)
    content_column=forms.IntegerField(label="概要列",min_value=1)
    air_date_column=forms.IntegerField(label="放送列",min_value=1)
    duration_column=forms.IntegerField(label="時間列",min_value=1)
class SourceSelectForm(forms.Form):
    SOURCE_CHOICES=[
        ("syoboi_calender","しょぼいカレンダー")
    ]
    q=forms.CharField(label="タイトル")
    source=forms.ChoiceField(choices=SOURCE_CHOICES, label="ソース")
class SourceSearchForm(forms.Form):
    titles=forms.MultipleChoiceField(label="追加するタイトルを選択",widget=forms.CheckboxSelectMultiple,choices=[])