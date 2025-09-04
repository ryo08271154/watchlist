from ..models import WatchRecord, Title, Tag, MyList, Episode
from django.utils import timezone
from django.db.models import Avg, IntegerField
from django.db.models import Exists, OuterRef, Q

import datetime
import random
# トップページ表示


def watched_date_month_topic(request):
    random_date = WatchRecord.objects.filter(user=request.user).exclude(
        watched_date=None).order_by("?")[0].watched_date
    topic_name = f"{random_date.year}年{random_date.month}月視聴"
    topic_description = f"{random_date.year}年{random_date.month}月に視聴したタイトル"
    topic_items = Title.objects.filter(watchrecord__user=request.user, watchrecord__status="watched",
                                       watchrecord__watched_date__year=random_date.year, watchrecord__watched_date__month=random_date.month)
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def watched_date_year_topic(request):
    random_date = WatchRecord.objects.filter(user=request.user).exclude(
        watched_date=None).order_by("?")[0].watched_date
    topic_name = f"{random_date.year}年視聴"
    topic_description = f"{random_date.year}年に視聴したタイトルをピックアップ"
    topic_items = Title.objects.filter(watchrecord__user=request.user, watchrecord__status="watched",
                                       watchrecord__watched_date__year=random_date.year).order_by("?")[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def tag_topic(request):
    random_tag = Tag.objects.order_by("?")[0]
    topic_name = f"{random_tag.name}"
    topic_description = f"{random_tag.description}"
    topic_items = Title.objects.filter(tags=random_tag)
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def air_date_month_topic(request):
    random_date = Title.objects.exclude(
        air_date=None).order_by("?")[0].air_date
    topic_name = f"{random_date.year}年{random_date.month}月放送"
    topic_description = f"{random_date.year}年{random_date.month}月に放送されたタイトル"
    topic_items = Title.objects.filter(
        air_date__year=random_date.year, air_date__month=random_date.month)
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def air_date_year_topic(request):
    random_date = Title.objects.exclude(
        air_date=None).order_by("?")[0].air_date
    topic_name = f"{random_date.year}年放送"
    topic_description = f"{random_date.year}年に放送されたタイトルをピックアップ"
    topic_items = Title.objects.filter(
        air_date__year=random_date.year).order_by("?")[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def my_list_topic(request):
    random_my_list = MyList.objects.exclude(is_public=False).order_by("?")[0]
    topic_name = f"{random_my_list.name}"
    topic_description = f"{random_my_list.description}"
    topic_items = MyList.objects.filter(id=random_my_list.id)[0].title.all()
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def today_episode_topic(request):
    topic_name = "24時間以内に放送されたエピソード"
    topic_description = "本日更新のエピソードをピックアップ"
    topic_items = Episode.objects.filter(air_date__range=[timezone.make_aware(datetime.datetime.now(
    )-datetime.timedelta(days=1)), timezone.make_aware(datetime.datetime.now())]).order_by("air_date")
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def recommended_topic(request):
    topic_name = "あなたへのおすすめ"
    topic_description = "あなたの最近の視聴傾向からおすすめのタイトルをピックアップ"
    watched_list = WatchRecord.objects.filter(user=request.user, status="watched").order_by(
        "-updated_at", "-watched_date")[:10]  # 直近10件の視聴履歴を取得
    recent_watch = WatchRecord.objects.filter(
        title=OuterRef('pk'),
        user=request.user,
        status="watched",
        watched_date__range=[
            timezone.now() - datetime.timedelta(days=182),
            timezone.now()
        ]
    )  # 過去6ヶ月以内に視聴したタイトルを除外する
    watched_genre_list = list(
        watched_list.values_list("title__genre", flat=True))
    watched_sub_genre_list = list(
        watched_list.values_list("title__sub_genre", flat=True))
    watched_tag_list = list(watched_list.values_list("title__tags", flat=True))
    average_rating = watched_list.aggregate(Avg("rating"))["rating__avg"]
    unique_genres = list(set(watched_genre_list))
    unique_sub_genres = list(set(watched_sub_genre_list))
    unique_tags = list(set(watched_tag_list))
    # 視聴履歴からジャンル、サブジャンル、タグを抽出
    candidates = list(Title.objects.filter(
        genre__in=unique_genres,
        sub_genre__in=unique_sub_genres,
        tags__in=unique_tags,
    ).annotate(
        recently_watched=Exists(recent_watch)
    ).filter(
        recently_watched=False
    ).distinct())
    random.shuffle(candidates)

    def get_score(title):
        score = 0
        title_avg_rating = WatchRecord.objects.filter(
            title=title).aggregate(Avg("rating"))["rating__avg"]
        # 平均評価に近い場合は加点
        if title_avg_rating:
            if average_rating - 10 <= title_avg_rating <= average_rating + 10:
                score += 3
        # サブジャンル、タグの数で加点
        for sub_genre in title.sub_genre.all():
            if sub_genre.id in unique_sub_genres:
                score += watched_sub_genre_list.count(sub_genre.id)
        for tag in title.tags.all():
            if tag.id in unique_tags:
                score += watched_tag_list.count(tag.id)
        # 長期間見ていない場合は加点
        last_watched = WatchRecord.objects.filter(
            title=title, user=request.user).order_by("-watched_date").first()
        if last_watched:
            last_watched_date = last_watched.watched_date if last_watched.watched_date else datetime.date.today()
        else:
            last_watched_date = datetime.date.today()
        if last_watched_date <= datetime.date.today() - datetime.timedelta(days=365):
            score += 3 * min(datetime.date.today().year -
                             last_watched_date.year, 5)  # 5年以上は5点
        elif last_watched_date >= datetime.date.today() - datetime.timedelta(days=90):
            score -= 5
        # 関連タイトルに最近見ている場合は減点
        for related_title in title.related_titles.all():
            related_last_watched = WatchRecord.objects.filter(
                user=request.user, title=related_title, status="watched").order_by("-watched_date").first()
            if related_last_watched:
                related_last_watched_date = related_last_watched.watched_date
                if related_last_watched_date >= datetime.date.today() - datetime.timedelta(days=90):
                    score -= max((datetime.date.today() -
                                 related_last_watched_date).days, 0) // 90
            if related_title.air_date >= datetime.date.today() - datetime.timedelta(days=365):
                score -= 3
        return score
    items = sorted(candidates, key=get_score, reverse=True)
    topic_items = []
    topic_items.extend(items[:15])
    return {"name": topic_name, "description": topic_description, "items": topic_items}
