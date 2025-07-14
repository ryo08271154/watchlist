from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from django.views.generic import ListView,DetailView,CreateView,UpdateView,FormView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.db.models import ManyToOneRel,ManyToManyRel,UUIDField
from .models import Title,Episode,Tag,Genre,SubGenre
from .forms import TitleForm,EpisodeForm,TitleFileImportForm,EpisodeFileImportForm,SourceSelectForm,SourceSearchForm
from .utils.embed import generate_embed_html

import csv
import io

import requests
import xml.etree.ElementTree as ET
import datetime
import re

class BaseExportView(LoginRequiredMixin,View):
    model=None
    order_by="air_date"
    def get_filter_kwargs(self):
        return {}
    def get(self,request):
        response=HttpResponse(content_type="text/csv;")
        filter_kwargs=self.get_filter_kwargs()
        export_data=self.model.objects.filter(**filter_kwargs).order_by(self.order_by).distinct()
        writer=csv.writer(response)
        fields=[]
        for field in self.model._meta.get_fields():
            if not isinstance(field,(ManyToOneRel,ManyToManyRel)):
                fields.append(field.name)
        writer.writerow(fields)
        for row in export_data.all().values(*fields):
            writer.writerow([row[field] for field in fields])
        return response

def related_titles_add(title):
    related_titles=Title.objects.filter(title__icontains=title.title).exclude(id=title.id).exclude(id__in=title.related_titles.all())
    if related_titles.exists():
        title.related_titles.add(*related_titles)
    for related_title in title.related_titles.all():
        title.related_titles.add(*related_title.related_titles.all().exclude(id=title.id).exclude(id__in=title.related_titles.all()))
    return title.related_titles.all()
def tags_add(title,field):
    tags=[]
    tags_name=re.findall(r"#\S+",getattr(title,field)) #コメントからタグを抽出する
    if tags_name:
        for tag in tags_name:
            tag=tag.replace("#","")
            tag,created=Tag.objects.get_or_create(name=tag)
            tags.append(tag)
        title.tags.add(*tags)
        setattr(title,field,re.sub(r"#.*\s*","",getattr(title,field))) #コメントからタグの部分を消す
        title.save()
    return tags
def tags_auto_add(title):
    tags=[]
    tags_name=[]
    #時期を追加
    air_date=title.air_date
    if air_date.month==1:
        season="冬"
    elif air_date.month==4:
        season="春"
    elif air_date.month==7:
        season="夏"
    elif air_date.month==10:
        season="秋"
    else:
        season=""
    if season!="":
        tags_name.append(f"{air_date.year}年{season}{title.genre.name}")
    tags_name.append(f"{title.air_date.year}年{title.genre.name}")
    for tag in tags_name:
        tag,created=Tag.objects.get_or_create(name=tag)
        tags.append(tag)
    title.tags.add(*tags)
    return tags
def csv_file_read(request_file):
    file=io.StringIO(request_file.read().decode("shift-jis"))
    return csv.reader(file)
#全タイトル表示
class TitleListView(LoginRequiredMixin,ListView):
    model=Title
    content_object_name="titles"
    template_name="titles/title_list.html"
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["titles"]=Title.objects.all()
        return context
#タイトル詳細表示
class TitleDetailView(LoginRequiredMixin,DetailView):
    model=Title
    content_object_name="title"
    template_name="titles/title_detail.html"
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["episodes"]=Episode.objects.filter(title=self.get_object())
        context["videos"]=generate_embed_html(self.get_object().content)
        return context
#タイトル追加
class TitleCreateView(LoginRequiredMixin,CreateView):
    model=Title
    form_class=TitleForm
    template_name="titles/form.html"
    def form_valid(self, form):
        title=form.save()
        tags_add(title,"content")
        tags_auto_add(title)
        related_titles_add(title)
        self.success_url=reverse_lazy("titles:title_detail",kwargs={"pk":title.id})
        return redirect(self.success_url)
#タイトル編集
class TitleEditView(LoginRequiredMixin,UpdateView):
    model=Title
    form_class=TitleForm
    template_name="titles/form.html"
    def form_valid(self, form):
        title=form.save()
        tags_add(title,"content")
        tags_auto_add(title)
        related_titles_add(title)
        self.success_url=reverse_lazy("titles:title_detail",kwargs={"pk":title.id})
        return redirect(self.success_url)
#タイトルをファイルからインポート
class TitleImportView(LoginRequiredMixin,FormView):
    form_class=TitleFileImportForm
    template_name="titles/form.html"
    success_url=reverse_lazy("titles:title_list")
    def form_valid(self, form):
        title_column=form.cleaned_data["title_column"]-1
        title_kana_column=form.cleaned_data["title_kana_column"]-1
        short_title_column=form.cleaned_data["short_title_column"]-1
        content_column=form.cleaned_data["content_column"]-1
        genre_column=form.cleaned_data["genre_column"]-1
        sub_genre_column=form.cleaned_data["sub_genre_column"]-1
        season_column=form.cleaned_data["season_column"]-1
        air_date_column=form.cleaned_data["air_date_column"]-1
        website_column=form.cleaned_data["website_column"]-1
        count=0
        try:
            reader=csv_file_read(self.request.FILES["file"])
        except Exception as e:
            messages.error(self.request,f"ファイルの読み込みに失敗しました")
            return super().form_invalid(form)
        titles=[]
        sub_genres=[]
        for r in reader:
            if count<form.cleaned_data["start_row"]-1:
                count+=1
                continue
            try:
                genre,created=Genre.objects.get_or_create(name=r[genre_column])
                if r[sub_genre_column]!="":
                    sub_genre,created=SubGenre.objects.get_or_create(name=r[sub_genre_column])
                else:
                    sub_genre=None
                sub_genres.append(sub_genre)
                title=Title(
                    title=r[title_column],
                    title_kana=r[title_kana_column],
                    short_title=r[short_title_column],
                    content=r[content_column],
                    genre=genre,
                    season=r[season_column],
                    air_date=datetime.date.fromisoformat(r[air_date_column]),
                    website=r[website_column])
                titles.append(title)
            except Exception as e:
                messages.error(self.request,f"一部データを追加できませんでした({e})：{r}")
        Title.objects.bulk_create(titles)
        for title,sub_genre in zip(titles,sub_genres):
            if sub_genre:
                title.sub_genre.add(sub_genre)
            related_titles_add(title)
            tags_auto_add(title)
        return redirect(self.success_url)
#タイトルのエピソード一覧を表示
class TitleEpisodeView(LoginRequiredMixin,ListView):
    model=Episode
    context_object_name="episodes"
    template_name="titles/title_episode_list.html"
    def get_queryset(self):
        return Episode.objects.filter(title=self.kwargs["pk"]).order_by("air_date").order_by("episode_number")
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["title"]=get_object_or_404(Title,id=self.kwargs["pk"])
        return context
#エピソード詳細表示
class EpisodeDetailView(LoginRequiredMixin,DetailView):
    model=Episode
    context_object_name="episode"
    template_name="titles/episode_detail.html"
#エピソード追加
class TitleEpisodeCreateView(LoginRequiredMixin,CreateView):
    model=Episode
    form_class=EpisodeForm
    template_name="titles/form.html"
    def form_valid(self,form):
        episode=form.save(commit=False)
        episode.title=get_object_or_404(Title,id=self.kwargs["pk"])
        episode.save()
        tags_add(episode,"content")
        episode.tags.add(*episode.title.tags.all())
        self.success_url=reverse_lazy("titles:episode_detail",kwargs={"pk":episode.id})
        return redirect(self.success_url)
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["title"]=get_object_or_404(Title,id=self.kwargs["pk"])
        return context
#エピソード編集
class EpisodeEditView(LoginRequiredMixin,UpdateView):
    model=Episode
    form_class=EpisodeForm
    context_object_name="episode"
    template_name="titles/form.html"
    def form_valid(self, form):
        episode=form.save()
        tags_add(episode,"content")
        episode.tags.add(*episode.title.tags.all())
        self.success_url=reverse_lazy("titles:episode_detail",kwargs={"pk":episode.id})
        return redirect(self.success_url)
#エピソードをファイルからインポート
class EpisodeImportView(LoginRequiredMixin,FormView):
    form_class=EpisodeFileImportForm
    template_name="titles/form.html"
    def form_valid(self, form):
        title=Title.objects.get(id=self.kwargs["pk"])
        self.success_url=reverse_lazy("titles:title_detail",kwargs={"pk":self.kwargs["pk"]})
        episode_title_column=form.cleaned_data["episode_title_column"]-1
        episode_number_column=form.cleaned_data["episode_number_column"]-1
        content_column=form.cleaned_data["content_column"]-1
        air_date_column=form.cleaned_data["air_date_column"]-1
        duration_column=form.cleaned_data["duration_column"]-1
        count=0
        try:
            reader=csv_file_read(self.request.FILES["file"])
        except Exception as e:
            messages.error(self.request,f"ファイルの読み込みに失敗しました")
            return super().form_invalid(form)
        episodes=[]
        for r in reader:
            if count<form.cleaned_data["start_row"]-1:
                count+=1
                continue
            try:
                episode=Episode(
                    title=title,
                    episode_title=r[episode_title_column],
                    episode_number=r[episode_number_column],
                    content=r[content_column],
                    air_date=datetime.date.fromisoformat([air_date_column]),
                    duration=r[duration_column]
                )
                episodes.append(episode)
            except:
                messages.error(self.request,f"一部データを追加できませんでした：{r}")
        Episode.objects.bulk_create(episodes)
        for episode in episodes:
            episode.tags.add(*episode.title.tags.all())
        return redirect(self.success_url)
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["title"]=get_object_or_404(Title,id=self.kwargs["pk"])
        return context

def syoboi_calender_title_search(title_name):
    r=requests.get(f"https://cal.syoboi.jp/json.php?Req=TitleSearch&Search={title_name}&Limit=15")
    result=r.json()["Titles"]
    if result is None:
        return []
    return list(result.values())
def syoboi_calender_title_get(tid):
    r=requests.get(f"https://cal.syoboi.jp/json.php?Req=TitleFull&TID={tid}")
    result=r.json()["Titles"]
    if result is None:
        return []
    return list(result.values())
#外部サイトからタイトルを取得して追加する
class TitleSourceImportView(LoginRequiredMixin,FormView):
    form_class=SourceSearchForm
    template_name="titles/search_form.html"
    success_url=reverse_lazy("titles:title_list")
    def get_form(self,form_class=None):
        form=super().get_form(form_class)
        if self.request.session.get("search_choices") and self.request.session.get("search_q")==self.request.GET.get("q"): #保存したのを使う
            form.fields["titles"].choices=self.request.session["search_choices"]
        elif self.request.GET.get("source")=="syoboi_calender" and self.request.method =="GET" and self.request.GET.get("q"): #検索して保存しておく
            search_result=syoboi_calender_title_search(self.request.GET.get("q"))
            form.fields["titles"].choices=[(title["TID"],title["Title"]) for title in search_result]
            self.request.session["search_choices"]=form.fields["titles"].choices
            self.request.session["search_q"]=self.request.GET.get("q")
        return form
    def form_valid(self, form):
        titles=[]
        if self.request.GET.get("source")=="syoboi_calender":
            GENRE_ID={"1":"アニメ","2":"ラジオ","3":"テレビ","4":"特撮","5":"アニメ関連番組","7":"アニメOVA","8":"映画","9":"アニメ","10":"アニメ"}
            selected_titles_id=form.cleaned_data["titles"]
            search_titles=syoboi_calender_title_get(",".join("".join(str(i)) for i in selected_titles_id))
            for search_title in search_titles:
                title_name=search_title["Title"]
                genre,created=Genre.objects.get_or_create(name=GENRE_ID[search_title["Cat"]])
                season=re.search(r"(\d+)",search_title["ShortTitle"])
                air_date=datetime.date(int(search_title["FirstYear"]),int(search_title["FirstMonth"]),1)
                website=re.search(r'\[\[公式\s+(\S+)\]\]',search_title["Comment"])
                media_urls=re.findall(r'\[\[(|Twitter.*?|X.*?|YouTube.*?|ニコニコ.*?)\s+(\S+)\]\]',search_title["Comment"])
                tid=search_title["TID"]
                title_search=Title.objects.filter(title=search_title["Title"],season=int(season.group()) if season else 1) #同じのが登録されてないか探す
                if title_search.count()>=1:
                    messages.error(self.request,f"すでにタイトルが登録されているため追加しませんでした：{title_name}")
                    continue
                elif title_search.count()==0:
                    title=Title(
                        title=title_name,
                        title_kana=search_title["TitleYomi"],
                        content="".join(url for name,url in media_urls),
                        genre=genre,
                        season=int(season.group()) if season else 1,
                        air_date=air_date,
                        website=website.group(1) if website else "",
                        source_website=f"https://cal.syoboi.jp/tid/{tid}"
                        )
                    titles.append(title)
        Title.objects.bulk_create(titles)
        for title in titles:
            related_titles=Title.objects.filter(title__icontains=title.title).exclude(id=title.id)
            if related_titles.exists():
                title.related_titles.add(*related_titles)
            for related_title in title.related_titles.all():
                title.related_titles.add(*related_title.related_titles.all().exclude(id=title.id).exclude(id__in=title.related_titles.all()))
            tags_auto_add(title)
        messages.success(self.request,f"{len(titles)}件のタイトルを追加しました")
        return redirect(self.success_url)
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["source_select_form"]=SourceSelectForm
        return context
def syoboi_calender_episode_get(title,selected_titles_id,title_episodes):
    tid=",".join("".join(str(i)) for i in selected_titles_id)
    # for tid in selected_tid:
    r=requests.get(f"https://cal.syoboi.jp/db.php/db?Command=ProgLookup&TID={tid}&JOIN=SubTitles")
    root=ET.fromstring(r.text)
    items=sorted(root.findall(".//ProgItem"),key=lambda x: int(x.find("TID").text)) #タイトルidで並べ替え
    items=sorted(root.findall(".//ProgItem"),key=lambda x: datetime.datetime.strptime(x.find("StTime").text,"%Y-%m-%d %H:%M:%S")) #放送開始時間順に並べ替え
    target_count=1
    episodes=[]
    update_episodes=[]
    while True:
        for item in items:
            item_count=int(item.find("Count").text or 0)
            if target_count==item_count and int(item.find("Deleted").text)==0 and int(item.find("Flag").text)!=8: #削除されているのと再放送は追加しない
                start_time=datetime.datetime.strptime(item.find("StTime").text,"%Y-%m-%d %H:%M:%S")
                end_time=datetime.datetime.strptime(item.find("EdTime").text,"%Y-%m-%d %H:%M:%S")
                duration=end_time-start_time
                minutes=int(duration.total_seconds()//60)
                episode_number=int(item.find("Count").text)
                pid=item.find("PID").text
                episode_search=title_episodes.filter(episode_number=episode_number) #同じのが登録されてないか探す
                if episode_search.count()>=1 and episode_search.first().episode_title=="" and item.find("STSubTitle").text:
                    #同じのが登録されていてエピソードタイトルが登録されていない場合登録する
                    episode=episode_search.first()
                    episode.episode_title=item.find("STSubTitle").text
                    episode.air_date=timezone.make_aware(start_time)
                    episode.source_website=f"https://cal.syoboi.jp/tid/{tid}/time#{pid}"
                    update_episodes.append(episode)
                elif episode_search.count()==0: #何も登録されていない場合
                    episode=Episode(
                        title=title,
                        episode_title=item.find("STSubTitle").text or "",
                        episode_number=episode_number,
                        content="",
                        air_date=timezone.make_aware(start_time),
                        duration=minutes,
                        source_website=f"https://cal.syoboi.jp/tid/{tid}/time#{pid}"
                    )
                    episodes.append(episode)
                target_count=item_count+1
                break
        else:
            break
    return episodes,update_episodes
#外部サイトからエピソードを取得して追加する
class TitleEpisodeSourceImportView(LoginRequiredMixin,FormView):
    form_class=SourceSearchForm
    template_name="titles/search_form.html"
    def get_form(self,form_class=None):
        form=super().get_form(form_class)
        if self.request.session.get("search_choices") and self.request.session.get("search_q")==self.request.GET.get("q"): #保存したのを使う
            form.fields["titles"].choices=self.request.session["search_choices"]
        elif self.request.GET.get("source")=="syoboi_calender" and self.request.method =="GET" and self.request.GET.get("q"): #検索して保存しておく
            search_result=syoboi_calender_title_search(self.request.GET.get("q"))
            form.fields["titles"].choices=[(title["TID"],title["Title"]) for title in search_result]
            self.request.session["search_choices"]=form.fields["titles"].choices
            self.request.session["search_q"]=self.request.GET.get("q")
        return form
    def form_valid(self,form):
        selected_titles_id=form.cleaned_data["titles"]
        title=Title.objects.get(id=self.kwargs["pk"])
        title_episodes=Episode.objects.filter(title=title).order_by("episode_number")
        self.success_url=reverse_lazy("titles:title_episodes",kwargs={"pk":title.id})
        if self.request.GET.get("source")=="syoboi_calender":
            episodes,update_episodes=syoboi_calender_episode_get(title,selected_titles_id,title_episodes)
        Episode.objects.bulk_create(episodes)
        for episode in episodes:
            episode.tags.add(*episode.title.tags.all())
        if update_episodes:
            Episode.objects.bulk_update(update_episodes,["episode_title","air_date","source_website"])
            messages.warning(self.request,f"{len(update_episodes)}件のエピソードを更新しました")
        messages.success(self.request,f"{len(episodes)}件のエピソードを追加しました")
        return redirect(self.success_url)
    def get_context_data(self, **kwargs):
        context=super().get_context_data(**kwargs)
        context["title"]=get_object_or_404(Title,id=self.kwargs["pk"])
        context["source_select_form"]=SourceSelectForm(initial={"q":get_object_or_404(Title,id=self.kwargs["pk"]).title})
        return context

class MyWatchScheduleView(LoginRequiredMixin,View):
    model=Episode
    template_name="titles/watch_schedule.html"
    def get(self,request):
        queryset=[]
        days=[]
        for day in range(8):
            start_time=datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)+datetime.timedelta(days=day)
            end_time=start_time+datetime.timedelta(hours=23,minutes=59,seconds=59)
            queryset.append(Episode.objects.filter(air_date__range=[timezone.make_aware(start_time),timezone.make_aware(end_time)]).order_by("air_date"))
            days.append(start_time)
        data=zip(queryset,days)
        today=datetime.datetime.now()
        last_week=datetime.datetime.now()-datetime.timedelta(days=7)
        next_week=datetime.datetime.now()+datetime.timedelta(days=7)
        return render(request,"titles/watch_schedule.html",{"data":data,"today":today,"last_week":last_week,"next_week":next_week})
class TitleExportView(BaseExportView):
    model=Title
class EpisodeExportView(BaseExportView):
    model=Episode