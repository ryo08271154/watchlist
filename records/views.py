from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, FormView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import WatchRecord, EpisodeWatchRecord, MyList, WatchMethod
from .forms import ReviewForm, EpisodeReviewForm, MyListForm, ReviewFileImportForm, ExportForm, MyListAddTitleForm
from titles.models import Title, Genre, SubGenre, Tag, Episode
from titles.views import BaseExportView, csv_file_read, tags_add
from django.db.models import Q, Sum
from django.utils import timezone
from .utils.topic import watched_date_month_topic, watched_date_year_topic, tag_topic, air_date_month_topic, air_date_year_topic, my_list_topic, today_episode_topic, recommended_topic

import csv
import io

import datetime
import random
import re

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import base64
import dateutil.relativedelta as relativedelta


def create_graph(x=[], y=[], x_label="", y_label="", title="", figsize=(8, 6), locator=ticker.MultipleLocator(1)):
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot()
    ax.bar(x, y)
    ax.yaxis.set_major_locator(locator)
    ax.set_xlabel(x_label, rotation=90, labelpad=10)
    ax.set_ylabel(y_label, rotation=90, labelpad=10)
    ax.set_title(title)
    fig.tight_layout()
    fig.autofmt_xdate()
    buffer = io.BytesIO()
    ax.figure.savefig(buffer, format='png')
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    return graph


class BaseReviewCreateView(LoginRequiredMixin, CreateView):
    template_name = "records/form.html"
    object_model = None
    field_name = None
    success_url_name = None

    def form_valid(self, form):
        review = form.save(commit=False)
        review.user = self.request.user
        setattr(review, self.field_name, self.object_model.objects.get(
            id=self.kwargs["pk"]))  # 元のタイトルやエピソードを追加する
        review.save()
        tags_add(review, "comment")
        messages.success(self.request, "レビューを追加しました")
        self.success_url = reverse_lazy(
            self.success_url_name, kwargs={"pk": review.id})
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.field_name] = get_object_or_404(
            self.object_model, id=self.kwargs["pk"])
        return context


class BaseReviewEditView(LoginRequiredMixin, UpdateView):
    template_name = "records/form.html"
    success_url_name = None

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        review = form.save()
        tags_add(review, "comment")
        self.success_url = reverse_lazy(
            self.success_url_name, kwargs={"pk": review.id})
        messages.success(self.request, "レビューを編集しました")
        return redirect(self.success_url)


class BaseReviewListView(LoginRequiredMixin, ListView):
    object_model = None
    field_name = None

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user, **{self.field_name: self.kwargs["pk"]})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.field_name] = get_object_or_404(
            self.object_model, id=self.kwargs["pk"])
        return context


class BaseReviewDetailView(LoginRequiredMixin, DetailView):
    context_object_name = "watch_record"

    def get_queryset(self):
        return super().get_queryset().filter(Q(user=self.request.user) | Q(user__is_public=True))


class IndexView(LoginRequiredMixin, View):
    def get(self, request):
        topics = []
        random_topic = 10  # ランダムに表示する数
        # 一番上固定
        topics.append(recommended_topic(request))
        topics.append(today_episode_topic(request))
        topics.append({"name": "視聴中", "description": "視聴中のタイトル", "items": Title.objects.filter(
            watchrecord__user=request.user, watchrecord__status="watching")})
        topics.append({"name": "今月視聴", "description": "今月視聴したタイトル", "items": Title.objects.filter(watchrecord__user=request.user, watchrecord__status="watched",
                      watchrecord__watched_date__year=datetime.date.today().year, watchrecord__watched_date__month=datetime.date.today().month)})
        # ランダムで表示
        topic_list = [watched_date_month_topic, watched_date_year_topic,
                      tag_topic, air_date_month_topic, air_date_year_topic, my_list_topic]
        if WatchRecord.objects.filter(user=request.user).count() <= random_topic:
            topic_list.remove(watched_date_month_topic)
            topic_list.remove(watched_date_year_topic)
        if Tag.objects.count() <= random_topic:
            topic_list.remove(tag_topic)
        if Title.objects.count() <= random_topic:
            topic_list.remove(air_date_month_topic)
            topic_list.remove(air_date_year_topic)
        if MyList.objects.exclude(is_public=False).count() <= random_topic:
            topic_list.remove(my_list_topic)
        if not topic_list:  # 全部消えた場合
            return render(request, "records/index.html", {"topics": topics})
        random_topic += len(topics)  # 固定の分を増やす
        while len(topics) < random_topic:
            choice = random.choice(topic_list)
            topic = choice(request)
            if topic["name"] in [i["name"] for i in topics]:  # 重複をさせないようにする
                continue
            topics.append(topic)
        return render(request, "records/index.html", {"topics": topics})


class ReviewCreateView(BaseReviewCreateView):  # レビューを追加する
    model = WatchRecord
    form_class = ReviewForm
    object_model = Title
    field_name = "title"
    success_url_name = "records:review_detail"


class ReviewEditView(BaseReviewEditView):  # レビューを編集する
    model = WatchRecord
    form_class = ReviewForm
    success_url_name = "records:review_detail"


class ReviewImportView(LoginRequiredMixin, FormView):  # レビューをファイルからインポート
    form_class = ReviewFileImportForm
    template_name = "records/form.html"
    success_url = reverse_lazy("titles:title_list")

    def form_valid(self, form):
        # -1は列番号を揃えるため
        title_column = form.cleaned_data["title_column"]-1
        genre_column = form.cleaned_data["genre_column"]-1
        air_date_column = form.cleaned_data["air_date_column"]-1
        season_column = form.cleaned_data["season_column"]-1
        comment_title_column = form.cleaned_data["comment_title_column"]-1
        comment_column = form.cleaned_data["comment_column"]-1
        watched_date_column = form.cleaned_data["watched_date_column"]-1
        rating_column = form.cleaned_data["rating_column"]-1
        status_column = form.cleaned_data["status_column"]-1
        watch_method_column = form.cleaned_data["watch_method_column"]-1
        count = 0
        try:
            reader = csv_file_read(self.request.FILES["file"])
        except Exception as e:
            messages.error(self.request, f"ファイルの読み込みに失敗しました")
            return super().form_invalid(form)
        reviews = []
        for r in reader:
            if count < form.cleaned_data["start_row"]-1:
                count += 1
                continue
            try:
                genre = Genre.objects.get(name=r[genre_column])
                title = Title.objects.get(
                    title=r[title_column], season=r[season_column], air_date=r[air_date_column], genre=genre)
                if r[status_column] == "視聴済み":
                    status = "watched"
                elif r[status_column] == "視聴中":
                    status = "watching"
                elif r[status_column] == "未視聴":
                    status = "not_watched"
                elif r[status_column] == "視聴中断":
                    status = "dropped"
                else:
                    status = ""
                watch_method, created = WatchMethod.objects.get_or_create(
                    name=r[watch_method_column])
                review = WatchRecord(
                    user=self.request.user,
                    title=title,
                    comment_title=r[comment_title_column],
                    comment=r[comment_column],
                    watched_date=datetime.date.fromisoformat(
                        r[watched_date_column]),
                    rating=r[rating_column],
                    status=status,
                    watch_method=watch_method,
                )
                reviews.append(review)
            except Title.DoesNotExist:
                messages.error(self.request, f"タイトルが見つかりませんでした：{r}")
            except ValueError:
                messages.error(self.request, f"日付の形式が正しくありません：{r}")
            except Exception as e:
                messages.error(self.request, f"一部データを追加できませんでした({e})：{r}")
        WatchRecord.objects.bulk_create(reviews)
        return super().form_valid(form)


class TitleReviewListView(BaseReviewListView):  # タイトルのレビューをすべて表示
    model = WatchRecord
    context_object_name = "watch_records"
    template_name = "records/title_review_list.html"
    object_model = Title
    field_name = "title"


class ReviewDetailView(BaseReviewDetailView):  # レビューの詳細を表示
    model = WatchRecord
    template_name = "records/review_detail.html"


class EpisodeCreateView(BaseReviewCreateView):  # エピソードにレビューを追加する
    model = EpisodeWatchRecord
    form_class = EpisodeReviewForm
    object_model = Episode
    field_name = "episode"
    success_url_name = "records:episode_review_detail"


class EpisodeReviewEditView(BaseReviewEditView):  # エピソードについたレビューを編集する
    model = EpisodeWatchRecord
    form_class = EpisodeReviewForm
    success_url_name = "records:episode_review_detail"


class EpisodeReviewListView(BaseReviewListView):  # エピソードについたコメントをすべて表示する
    model = EpisodeWatchRecord
    context_object_name = "watch_records"
    template_name = "records/episode_review_list.html"
    object_model = Episode
    field_name = "episode"


class EpisodeReviewDetailView(BaseReviewDetailView):  # エピソードレビューの詳細を表示
    model = EpisodeWatchRecord
    template_name = "records/episode_review_detail.html"


class MyListView(LoginRequiredMixin, ListView):  # マイリスト一覧表示
    model = MyList
    context_object_name = "my_lists"
    template_name = "records/mylist.html"

    def get_queryset(self):
        return MyList.objects.filter(user=self.request.user)


class MyListDetailView(LoginRequiredMixin, DetailView):  # マイリストの詳細を表示
    model = MyList
    context_object_name = "mylist"
    template_name = "records/mylist_detail.html"

    def get_queryset(self):
        return MyList.objects.filter(Q(user=self.request.user) | Q(is_public=True))


class MyListCreateView(LoginRequiredMixin, CreateView):  # マイリストを作成
    model = MyList
    form_class = MyListForm
    template_name = "records/form.html"

    def form_valid(self, form):
        mylist = form.save(commit=False)
        mylist.user = self.request.user
        mylist.save()
        tags_add(mylist, "description")
        self.success_url = reverse_lazy(
            "records:mylist_detail", kwargs={"pk": mylist.id})
        messages.success(self.request, "リストを作成しました")
        return redirect(self.success_url)


class MyListEditView(LoginRequiredMixin, UpdateView):  # マイリストを編集
    model = MyList
    form_class = MyListForm
    template_name = "records/form.html"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def form_valid(self, form):
        mylist = form.save()
        self.success_url = reverse_lazy(
            "records:mylist_detail", kwargs={"pk": mylist.id})
        tags_add(mylist, "description")
        messages.success(self.request, "リストを編集しました")
        return redirect(self.success_url)


class MyListAddTitleView(LoginRequiredMixin, FormView):  # マイリストにタイトルを追加
    form_class = MyListAddTitleForm
    template_name = "records/form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user_mylists = MyList.objects.filter(
            user=self.request.user).exclude(titles__in=[self.kwargs["pk"]])
        form.fields["mylists"].choices = [
            (mylist.id, mylist.name) for mylist in user_mylists]
        return form

    def form_valid(self, form):
        add_mylists = form.cleaned_data["mylists"]
        for mylist in add_mylists:
            mylist = MyList.objects.get(id=mylist)
            mylist.titles.add(Title.objects.get(id=self.kwargs["pk"]))
        messages.success(
            self.request, f"{len(add_mylists)}件のマイリストに追加しました")
        self.success_url = reverse_lazy("titles:title_detail", kwargs={
                                        "pk": self.kwargs["pk"]})
        return super().form_valid(form)


class TagView(LoginRequiredMixin, ListView):  # タグ一覧表示
    model = Tag
    context_object_name = "tags"
    template_name = "records/tag_list.html"

    def get_queryset(self):
        return super().get_queryset().order_by("name")


class TagDetailView(LoginRequiredMixin, DetailView):  # タグ詳細表示
    model = Tag
    context_object_name = "tag"
    template_name = "records/tag_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titles"] = Title.objects.filter(tags=self.get_object())
        context["episodes"] = Episode.objects.filter(tags=self.get_object())
        context["watch_records"] = WatchRecord.objects.filter(
            Q(tags=self.get_object()) & (Q(user=self.request.user) | Q(user__is_public=True)))
        context["episode_watch_records"] = EpisodeWatchRecord.objects.filter(
            Q(tags=self.get_object()) & (Q(user=self.request.user) | Q(user__is_public=True)))
        context["my_lists"] = MyList.objects.filter(
            Q(tags=self.get_object()) & (Q(user=self.request.user) | Q(is_public=True)))
        return context


def search_index_view(request):  # 検索
    genres = Genre.objects.all()
    sub_genres = SubGenre.objects.all()
    air_date = Title.objects.all().order_by(
        "air_date").values_list("air_date", flat=True).distinct()
    tag = Tag.objects.all().order_by("?")[:10].values_list("name", flat=True)
    watched_date = WatchRecord.objects.filter(user=request.user).order_by(
        "watched_date").values_list("watched_date", flat=True).distinct()
    status = [["watching", "視聴中"], ["watched", "視聴済み"],
              ["not_watched", "未視聴"], ["dropped", "視聴中断"]]
    watch_method = WatchMethod.objects.order_by(
        "name").values_list("name", flat=True).distinct()
    keywords = []
    keywords.append(Genre.objects.all().order_by("?")[0].name)
    keywords.append(SubGenre.objects.all().order_by("?")[0].name)
    keywords.extend(tag)
    context = {"genres": genres, "sub_genres": sub_genres, "air_date": air_date, "keywords": keywords,
               "watched_date": watched_date, "status": status, "watch_method": watch_method}
    return render(request, "records/search_index.html", context)


class SearchView(LoginRequiredMixin, View):
    context_object_name = "titles"
    template_name = "records/search.html"

    def get(self, request):
        titles = Title.objects.all()
        episodes = Episode.objects.all()
        watch_records = WatchRecord.objects.filter(Q(user=request.user))
        episode_watch_records = EpisodeWatchRecord.objects.filter(
            Q(user=request.user))
        my_list = MyList.objects.filter(
            Q(user=request.user) | Q(is_public=True))
        keywords = self.request.GET.get('q')
        search_type = self.request.GET.get("type")
        genre = self.request.GET.get("genre")
        sub_genre = self.request.GET.get("sub_genre")
        season = self.request.GET.get("season")
        air_date = self.request.GET.get("air_date")
        tag = self.request.GET.get("tag")
        episode_number = self.request.GET.get("episode_number")
        duration = self.request.GET.get("duration")
        watched_date = self.request.GET.get("watched_date")
        rating = self.request.GET.get("rating")
        status = self.request.GET.get("status")
        watch_method = self.request.GET.get("watch_method")
        title_conditions = {("genre__name", genre), ("sub_genre__name", sub_genre), (
            "season", season), ("air_date__icontains", air_date), ("tags__name", tag)}
        episode_conditions = {("title__genre__name", genre), ("title__sub_genre__name", sub_genre), ("title__season", season), (
            "episode_number", episode_number), ("duration", duration), ("air_date__icontains", air_date), ("tags__name", tag)}
        watch_record_conditions = {("title__genre__name", genre), ("title__sub_genre__name", sub_genre), ("title__season", season), ("title__air_date__icontains", air_date), (
            "watched_date__icontains", watched_date), ("rating", rating), ("status", status), ("watch_method__name", watch_method), ("tags__name", tag)}
        episode_watch_record_conditions = {("episode__title__genre__name", genre), ("episode__title__sub_genre__name", sub_genre), ("episode__title__season", season), (
            "episode__title__air_date__icontains", air_date), ("watched_date__icontains", watched_date), ("rating", rating), ("status", status), ("watch_method__name", watch_method), ("tags__name", tag)}
        mylist_conditions = {("tags__name", tag)}
        conditions = [genre, sub_genre, season, air_date, tag, episode_number,
                      duration, watched_date, rating, status, watch_method]
        # キーワードが入力されてないとき検索トップ表示
        if not keywords and not search_type and not any(conditions):
            if keywords == "" or search_type == "" or any(i == "" for i in conditions):
                return redirect("records:search")
            return search_index_view(request)
        if search_type:
            search_type = search_type.split(",")
        else:  # 検索範囲が指定されてない場合検索タイプを設定
            search_type = ["title", "record",
                           "episode_record", "episode", "mylist"]
        if genre or sub_genre or season or air_date:
            if "mylist" in search_type:
                search_type.remove("mylist")
        if episode_number or duration:
            if "title" in search_type:
                search_type.remove("title")
            if "mylist" in search_type:
                search_type.remove("mylist")
        if rating or status or watch_method or watched_date:
            if "title" in search_type:
                search_type.remove("title")
            if "episode" in search_type:
                search_type.remove("episode")
            if "mylist" in search_type:
                search_type.remove("mylist")

        def apply_filters(queryset, conditions):
            for field, value in conditions:
                if value:
                    queryset = queryset.filter(**{field: value})
            return queryset
        titles = apply_filters(titles, title_conditions)
        episodes = apply_filters(episodes, episode_conditions)
        watch_records = apply_filters(watch_records, watch_record_conditions)
        episode_watch_records = apply_filters(
            episode_watch_records, episode_watch_record_conditions)
        my_list = apply_filters(my_list, mylist_conditions)
        if keywords:
            keywords = keywords.split()
            for keyword in keywords:
                if "title" in search_type:
                    titles = titles.filter(Q(title__icontains=keyword) | Q(title_kana__icontains=keyword) | Q(short_title__icontains=keyword) | Q(content__icontains=keyword) | Q(
                        air_date__icontains=keyword) | Q(genre__name__icontains=keyword) | Q(sub_genre__name__icontains=keyword) | Q(tags__name__icontains=keyword)).distinct()
                if "record" in search_type:
                    watch_records = watch_records.filter((Q(comment_title__icontains=keyword) | Q(comment__icontains=keyword) | Q(
                        watched_date__icontains=keyword) | Q(status=keyword)) & (Q(user=request.user))).distinct()
                if "episode_record" in search_type:
                    episode_watch_records = episode_watch_records.filter((Q(comment_title__icontains=keyword) | Q(
                        comment__icontains=keyword) | Q(watched_date__icontains=keyword) | Q(status=keyword)) & (Q(user=request.user))).distinct()
                if "episode" in search_type:
                    episodes = episodes.filter(Q(title__title__icontains=keyword) | Q(episode_title__icontains=keyword) | Q(content__icontains=keyword) | Q(
                        air_date__icontains=keyword) | Q(duration__icontains=keyword) | Q(tags__name__icontains=keyword)).distinct()
                if "mylist" in search_type:
                    my_list = my_list.filter((Q(name__icontains=keyword) | Q(description__icontains=keyword)) & (
                        Q(user=request.user) | Q(is_public=True))).distinct()
        if search_type:
            context = {"search_type": search_type}
            if "title" in search_type:
                context.update({"titles": titles})
            if "episode" in search_type:
                context.update({"episodes": episodes})
            if "record" in search_type:
                context.update({"watch_records": watch_records})
            if "episode_record" in search_type:
                context.update(
                    {"episode_watch_records": episode_watch_records})
            if "mylist" in search_type:
                context.update({"my_list": my_list})
        return render(request, "records/search_result.html", context)


class MypageView(LoginRequiredMixin, View):
    def get(self, request):
        watched_titles = WatchRecord.objects.filter(status="watched", user=request.user).order_by(
            "watched_date").order_by("-updated_at")[:10]
        watching_titles = WatchRecord.objects.filter(
            status="watching", user=request.user).order_by("-updated_at")[:10]
        not_watched_titles = WatchRecord.objects.filter(
            status="not_watched", user=request.user).order_by("-updated_at")[:10]
        dropped_titles = WatchRecord.objects.filter(
            status="dropped", user=request.user).order_by("-updated_at")
        none_watched_titles = WatchRecord.objects.filter(
            status="", user=request.user).order_by("-updated_at")[:10]
        my_lists = MyList.objects.filter(
            user=request.user).order_by("-updated_at")[:10]
        return render(request, "records/mypage.html", {"watched_titles": watched_titles, "watching_titles": watching_titles, "not_watched_titles": not_watched_titles, "dropped_titles": dropped_titles, "none_watched_titles": none_watched_titles, "my_lists": my_lists})


class MyReviewListView(LoginRequiredMixin, ListView):
    template_name = "records/myreview.html"
    model = WatchRecord
    ordering = "-watched_date"
    context_object_name = "watch_records"

    def get_queryset(self):
        if self.request.GET.get("year"):
            return super().get_queryset().filter(user=self.request.user, watched_date__year=self.request.GET.get("year"))
        else:
            now_year = datetime.date.today()
            last_year = now_year-relativedelta.relativedelta(years=1)
            return super().get_queryset().filter(user=self.request.user, watched_date__range=[last_year, now_year])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["min_year"] = WatchRecord.objects.filter(user=self.request.user).exclude(
            watched_date=None).order_by("watched_date").values_list("watched_date__year", flat=True).first()  # 最小年を取得
        context["max_year"] = datetime.date.today().year
        if self.request.GET.get("year"):
            year = datetime.date(
                year=int(self.request.GET.get("year")), month=12, day=1)
            context["year"] = year.year
        else:
            year = datetime.date.today()
        context["months"] = [year.replace(
            day=1)-relativedelta.relativedelta(months=m) for m in range(12)]  # 1年分の月を取得
        return context


def watched_series(request):
    watched = WatchRecord.objects.filter(user=request.user, status="watched")
    watched_series = []
    added_keywords = set()
    for title in watched:
        title_name = title.title.title
        if not any(keyword in title_name or title_name in keyword for keyword in added_keywords):
            watched_series.append(title)
            added_keywords.add(title.title.title)
            for related_title in title.title.related_titles.all():
                added_keywords.add(related_title.title)
    return len(watched_series)


def watched_month(request, month):
    month_watched_count = []
    label_month = []
    for m in month:
        month_watched = WatchRecord.objects.filter(
            user=request.user, watched_date__year=m.year, watched_date__month=m.month, status="watched")
        month_watched_count.append(month_watched.count())
        label_month.append(m.strftime("%m"))
    return create_graph(label_month, month_watched_count, "month", "number of views", "Number of titles viewed per month")


def watched_season(request):  # 時期別視聴数
    month = []
    month_watched_count = []
    season_title = []
    label_month = []
    today = datetime.date.today().replace(day=1)
    year = 15
    for y in range(year+1):
        temp_season = today-relativedelta.relativedelta(years=(year-y))
        month.append(temp_season.replace(month=1))  # 冬
        month.append(temp_season.replace(month=4))  # 春
        month.append(temp_season.replace(month=7))  # 夏
        month.append(temp_season.replace(month=10))  # 秋
    for m in month:
        season_title = Title.objects.filter(
            air_date__year=m.year, air_date__month=m.month)
        temp_count = 0
        for title in season_title:
            if title and WatchRecord.objects.filter(user=request.user, title=title, status="watched").exists():
                temp_count += 1
        month_watched_count.append(temp_count)
        label_month.append((m.strftime("%Y %m")).replace(" 01", " winter").replace(
            " 04", " spring").replace(" 07", " summer").replace(" 10", " fall"))
    return create_graph(label_month, month_watched_count, "season", "number of views", "Viewership by broadcast period", figsize=(20, 6))


def total_watched_duration(reviews):  # 合計時間を調べる
    total_duration = 0
    for review in reviews:
        for episode in review.title.episodes.all():
            total_duration += episode.duration
    return round(total_duration/60, 2)  # エピソードすべての合計時間


def watched_duration(request, month):  # 月間視聴時間グラフとすべての合計時間を求める
    watched = WatchRecord.objects.filter(user=request.user, status="watched")
    total_duration = total_watched_duration(watched)
    month_watched_duration = []
    label_month = []
    for m in month:  # 1年以内のグラフ
        month_watched = WatchRecord.objects.filter(
            user=request.user, status="watched", watched_date__year=m.year, watched_date__month=m.month)
        month_total_duration = total_watched_duration(month_watched)
        month_watched_duration.append(month_total_duration)  # エピソードすべての合計時間
        label_month.append(m.strftime("%m"))
    return total_duration, create_graph(label_month, month_watched_duration, "month", "viewing time", "monthly viewing time", locator=ticker.AutoLocator())


class MyStatsView(LoginRequiredMixin, View):
    def get(self, request):
        month = []
        today = datetime.date.today().replace(day=1)
        for m in range(12):
            # 今月から1年以内のみ表示する
            month.append((today-relativedelta.relativedelta(months=(11-m))))
        total_watched = WatchRecord.objects.filter(
            user=request.user, status="watched").values("title").distinct().count()
        watched_count = WatchRecord.objects.filter(
            user=request.user, status="watched").count()
        total_watched_series = watched_series(request)
        total_episode = EpisodeWatchRecord.objects.filter(
            user=request.user, status="watched").values("episode").distinct().count()
        episode_count = EpisodeWatchRecord.objects.filter(
            user=request.user, status="watched").count()
        total_duration, watched_duration_graph = watched_duration(
            request, month)
        watched_graph = watched_month(request, month)
        watched_season_graph = watched_season(request)
        return render(request, "records/mystats.html", {"total_watched": total_watched, "watched_count": watched_count, "total_watched_series": total_watched_series, "episode_count": episode_count, "total_episode": total_episode, "total_duration": total_duration, "watched_graph": watched_graph, "watched_duration_graph": watched_duration_graph, "watched_season_graph": watched_season_graph})


class ReviewExportView(BaseExportView):
    model = WatchRecord
    order_by = "watched_date"

    def get_filter_kwargs(self):
        return {"user": self.request.user}


class EpisodeReviewExportView(BaseExportView):
    model = EpisodeWatchRecord
    order_by = "watched_date"

    def get_filter_kwargs(self):
        return {"user": self.request.user}


class MyListExportView(BaseExportView):
    model = MyList
    order_by = "created_at"

    def get_filter_kwargs(self):
        return {"user": self.request.user}


class ExportView(LoginRequiredMixin, TemplateView):
    template_name = "records/export.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        forms = []
        export_models = [(Title, "titles", "タイトル"), (Episode, "episodes", "エピソード"), (WatchRecord, "reviews",
                                                                                     "レビュー"), (EpisodeWatchRecord, "episode_reviews", "エピソードレビュー"), (MyList, "mylists", "マイリスト")]
        for export_model, export_model_name, display_name in export_models:
            form = ExportForm()
            form.auto_id = False  # 同じ名前の選択肢があるため
            choices = [(field.name, field.verbose_name)
                       for field in export_model._meta.fields]
            form.fields["fields"].choices = choices
            form.initial["fields"] = [choice for choice, _ in choices]
            forms.append((form, export_model_name, display_name))
        context["forms"] = forms
        return context
