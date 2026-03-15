from ..models import WatchRecord, Title, Tag, MyList, Episode, EpisodeWatchRecord
from django.utils import timezone
from django.db.models import Avg, IntegerField, Exists, OuterRef, Q, Max, Count
from django.urls import reverse

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
    return {"name": topic_name, "description": topic_description, "items": topic_items, "url": reverse("records:search")+f"?watched_date={random_date.year}-{random_date.month:02d}"}


def watched_date_year_topic(request):
    random_date = WatchRecord.objects.filter(user=request.user).exclude(
        watched_date=None).order_by("?")[0].watched_date
    topic_name = f"{random_date.year}年視聴"
    topic_description = f"{random_date.year}年に視聴したタイトルをピックアップ"
    topic_items = Title.objects.filter(watchrecord__user=request.user, watchrecord__status="watched",
                                       watchrecord__watched_date__year=random_date.year).order_by("?")[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items, "url": reverse("records:myreview")+f"?year={random_date.year}"}


def tag_topic(request):
    random_tag = Tag.objects.order_by("?")[0]
    topic_name = f"{random_tag.name}"
    topic_description = f"{random_tag.description}"
    topic_items = Title.objects.filter(tags=random_tag)
    return {"name": topic_name, "description": topic_description, "items": topic_items, "url": reverse("records:tag_detail", args=[random_tag.id])}


def air_date_month_topic(request):
    random_date = Title.objects.exclude(
        air_date=None).order_by("?")[0].air_date
    topic_name = f"{random_date.year}年{random_date.month}月放送"
    topic_description = f"{random_date.year}年{random_date.month}月に放送されたタイトル"
    topic_items = Title.objects.filter(
        air_date__year=random_date.year, air_date__month=random_date.month)
    return {"name": topic_name, "description": topic_description, "items": topic_items, "url": reverse("records:search")+f"?air_date={random_date.year}-{random_date.month:02d}"}


def air_date_year_topic(request):
    random_date = Title.objects.exclude(
        air_date=None).order_by("?")[0].air_date
    topic_name = f"{random_date.year}年放送"
    topic_description = f"{random_date.year}年に放送されたタイトルをピックアップ"
    topic_items = Title.objects.filter(
        air_date__year=random_date.year).order_by("?")[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items, "url": reverse("records:search")+f"?air_date={random_date.year}"}


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
    return {"name": topic_name, "description": topic_description, "items": topic_items, "type": "episode", "url": reverse("titles:watch_schedule")}


def recommended_topic(request):
    topic_name = "あなたへのおすすめ"
    topic_description = "あなたの最近の視聴傾向からおすすめのタイトルをピックアップ"
    watched_list = WatchRecord.objects.filter(user=request.user, status="watched").order_by(
        "-updated_at", "-watched_date").select_related("title")[:10]  # 直近10件の視聴履歴を取得
    recent_watch = WatchRecord.objects.filter(
        title=OuterRef("pk"),
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
    average_rating = watched_list.aggregate(Avg("rating"))["rating__avg"] or 0
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
    ).distinct().select_related("genre").prefetch_related("sub_genre", "tags", "related_titles"))
    random.shuffle(candidates)

    # 候補タイトル群のIDリスト
    candidate_ids = [t.id for t in candidates]

    # タイトルごとの平均評価を一括取得
    title_avg_qs = WatchRecord.objects.filter(
        title__in=candidate_ids).values("title").annotate(avg=Avg("rating"))
    title_avg_map = {item["title"]: item["avg"] for item in title_avg_qs}

    # ユーザーが各タイトルを最後に見た日を一括取得
    last_watched_qs = WatchRecord.objects.filter(
        title__in=candidate_ids, user=request.user).values("title").annotate(last=Max("watched_date"))
    last_watched_map = {item["title"]: item["last"]
                        for item in last_watched_qs}

    # 候補の関連タイトルIDを収集して、ユーザーの関連タイトルに対する最終視聴日を一括取得
    related_ids = set()
    for t in candidates:
        related_ids.update([rt.id for rt in t.related_titles.all()])
    related_last_map = {}
    if related_ids:
        related_last_qs = WatchRecord.objects.filter(title__in=list(
            related_ids), user=request.user, status="watched").values("title").annotate(last=Max("watched_date"))
        related_last_map = {item["title"]: item["last"]
                            for item in related_last_qs}

    def to_date(d):
        if d is None:
            return None
        return d.date() if isinstance(d, datetime.datetime) else d

    def get_score(title):
        score = 0

        # キャッシュされた平均評価を参照
        title_avg_rating = title_avg_map.get(title.id)
        if title_avg_rating:
            if average_rating - 10 <= title_avg_rating <= average_rating + 10:
                score += 3

        # サブジャンル、タグの数で加点（prefetch済みなのでDB再問い合わせなし）
        for sub_genre in title.sub_genre.all():
            if sub_genre.id in unique_sub_genres:
                score += watched_sub_genre_list.count(sub_genre.id)
        for tag in title.tags.all():
            if tag.id in unique_tags:
                score += watched_tag_list.count(tag.id)

        # 長期間見ていない場合は加点（ユーザーごとの最終視聴日をマップから取得）
        lw = last_watched_map.get(title.id)
        last_watched_date = to_date(lw) if lw else None
        if not last_watched_date:
            last_watched_date = datetime.date.today()
        if last_watched_date <= datetime.date.today() - datetime.timedelta(days=365):
            score += 3 * min(datetime.date.today().year -
                             last_watched_date.year, 5)
        elif last_watched_date >= datetime.date.today() - datetime.timedelta(days=90):
            score -= 5

        # 関連タイトルに最近見ている場合は減点（関連タイトルの最終視聴日マップを参照）
        for related_title in title.related_titles.all():
            r_last = related_last_map.get(related_title.id)
            r_last_date = to_date(r_last) if r_last else None
            if r_last_date and r_last_date >= datetime.date.today() - datetime.timedelta(days=90):
                score -= max((datetime.date.today() -
                             r_last_date).days, 0) // 90
            if related_title.air_date and related_title.air_date >= datetime.date.today() - datetime.timedelta(days=365):
                score -= 3
        return score

    items = sorted(candidates, key=get_score, reverse=True)
    topic_items = []
    topic_items.extend(items[:15])
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def next_episode_topic(request):
    topic_name = "続きを見る"
    topic_description = "視聴中の作品の次のエピソード"
    watching_records = WatchRecord.objects.filter(
        user=request.user, status="watching").select_related("title")
    next_episodes = []
    for record in watching_records:
        last_watched_episode = EpisodeWatchRecord.objects.filter(
            user=request.user, episode__title=record.title, status="watched"
        ).order_by("-episode__episode_number").select_related("episode").first()

        if last_watched_episode:
            next_episode_number = last_watched_episode.episode.episode_number + 1
        else:
            next_episode_number = 1

        next_episode = Episode.objects.filter(
            title=record.title, episode_number=next_episode_number, air_date__lte=timezone.now()
        ).first()

        if next_episode:
            next_episodes.append(next_episode)
    return {"name": topic_name, "description": topic_description, "items": next_episodes, "type": "episode"}


def get_rated_items(request, model, min_rating=None, max_rating=None, field_name="watchrecord"):
    rating_field = f"{field_name}__rating"
    user_field = f"{field_name}__user"
    queryset = model.objects.annotate(avg_rating=Avg(
        rating_field)).filter(**{user_field: request.user})
    if min_rating is not None:
        queryset = queryset.filter(avg_rating__gte=min_rating)
    if max_rating is not None:
        queryset = queryset.filter(avg_rating__lte=max_rating)
    return queryset.order_by("?")


def high_rated_titles_topic(request):
    topic_name = "高評価タイトル"
    topic_description = "あなたが高く評価したタイトル"
    topic_items = get_rated_items(request, Title, min_rating=80)[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items, "url": reverse("records:myreview")}


def low_rated_titles_topic(request):
    topic_name = "低評価タイトル"
    topic_description = "あなたが低く評価したタイトル"
    topic_items = get_rated_items(request, Title, max_rating=30)[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def high_rated_episodes_topic(request):
    topic_name = "高評価エピソード"
    topic_description = "あなたが高く評価したエピソード"
    topic_items = get_rated_items(
        request, Episode, min_rating=80, field_name="episodewatchrecord")[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items, "type": "episode"}


def low_rated_episodes_topic(request):
    topic_name = "低評価エピソード"
    topic_description = "あなたが低く評価したエピソード"
    topic_items = get_rated_items(
        request, Episode, max_rating=30, field_name="episodewatchrecord")[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items, "type": "episode"}


def recent_added_topic(request):
    topic_name = "最近追加されたタイトル"
    topic_description = "最近追加されたタイトルをピックアップ"
    topic_items = Title.objects.order_by("-created_at")[:10]
    return {"name": topic_name, "description": topic_description, "items": topic_items, "url": reverse("titles:title_list")+"?sort=-created_at"}


def most_watched_topic(request):
    topic_name = "視聴回数が多いタイトル"
    topic_description = "視聴回数が多いタイトルをピックアップ"
    topic_items = list(Title.objects.annotate(watch_count=Count("watchrecord", filter=Q(
        watchrecord__user=request.user, watchrecord__status="watched"))).order_by("-watch_count")[:30])
    random.shuffle(topic_items)
    return {"name": topic_name, "description": topic_description, "items": topic_items}


def menu_topic(request):
    topic_name = "メニュー"
    topic_description = "様々な機能への入り口"
    topic_items = [
        {"main_title": "マイページ", "url": reverse("records:mypage"),
            "content": "あなたの視聴状況を確認できます。"},
        {"main_title": "マイレビュー", "url": reverse("records:myreview"),
            "content": "あなたが書いたレビューの一覧です。"},
        {"main_title": "マイリスト", "url": reverse("records:mylist"),
            "content": "作成したマイリストを表示・管理します。"},
        {"main_title": "統計", "url": reverse("records:mystats"),
            "content": "あなたの視聴データをグラフで可視化します。"},
        {"main_title": "検索", "url": reverse("records:search"),
            "content": "タイトル、エピソード、レビューなどを検索します。"},
        {"main_title": "エクスポート", "url": reverse("records:export"),
            "content": "あなたのデータをCSVファイルにエクスポートします。"},
    ]
    return {"name": topic_name, "description": topic_description, "items": topic_items, "type": "custom"}


def build_sections(request):
    topics = []
    random_topic = 10  # ランダムに表示する数
    # 一番上固定
    topics.append(recommended_topic(request))
    topics.append(next_episode_topic(request))
    topics.append(today_episode_topic(request))
    topics.append({"name": "視聴中", "description": "視聴中のタイトル", "items": Title.objects.filter(
        watchrecord__user=request.user, watchrecord__status="watching"), "url": reverse("records:search") + "?status=watching"})
    topics.append({"name": "最近視聴したタイトル", "description": "最近視聴したタイトル", "items": Title.objects.filter(
        watchrecord__user=request.user, watchrecord__status="watched").order_by("-watchrecord__created_at")[:10], "url": reverse("records:myreview")})
    topics.append({"name": "最近視聴したエピソード", "description": "最近視聴したエピソード", "items": Episode.objects.filter(
        episodewatchrecord__user=request.user, episodewatchrecord__status="watched").order_by("-episodewatchrecord__created_at")[:10], "url": reverse("records:myreview")+"?type=episode_record", "type": "episode"})

    # ランダムで表示
    topic_list = [watched_date_month_topic, watched_date_year_topic, tag_topic, air_date_month_topic, air_date_year_topic, my_list_topic,
                  high_rated_titles_topic, low_rated_titles_topic, high_rated_episodes_topic, low_rated_episodes_topic, recent_added_topic, menu_topic, most_watched_topic]
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
        raise Exception("セクションを生成できませんでした。条件を満たすデータが不足しています。")
    random_topic += len(topics)  # 固定の分を増やす
    while len(topics) < random_topic:
        choice = random.choice(topic_list)
        topic = choice(request)
        if topic["name"] in [i["name"] for i in topics]:  # 重複をさせないようにする
            continue
        topics.append(topic)
    sections = []
    for t in topics:
        item_type = t.get("type", "title")
        sections.append({
            "id": t["name"],
            "section_url": "#" if not t.get("url") else t["url"],
            "section_name": t["name"],
            "section_description": t["description"],
            "item_type": item_type,
            "items": t["items"],
        })
    return sections
