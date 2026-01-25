import requests
import datetime
import re
from urllib.parse import urlparse
import xml.etree.ElementTree as ET
from ..models import Genre, Title, Episode
from django.utils import timezone
from django.contrib import messages


def search_syoboi_calendar_titles(title_name):
    try:
        r = requests.get(
            f"https://cal.syoboi.jp/json.php?Req=TitleSearch&Search={title_name}&Limit=15")
    except:
        return []
    if r.status_code != 200:
        return []
    result = r.json()["Titles"]
    if result is None:
        return []
    return list(result.values())


def get_syoboi_calendar_title(tid):
    try:
        r = requests.get(
            f"https://cal.syoboi.jp/json.php?Req=TitleFull&TID={tid}")
    except:
        return []
    if r.status_code != 200:
        return []
    result = r.json()["Titles"]
    if result is None:
        return []
    return list(result.values())


def import_syoboi_titles(request, selected_titles_id):
    titles = []
    GENRE_ID = {"1": "アニメ", "2": "ラジオ", "3": "テレビ", "4": "特撮",
                "5": "アニメ関連番組", "7": "アニメOVA", "8": "映画", "9": "アニメ", "10": "アニメ"}
    search_titles = get_syoboi_calendar_title(
        ",".join("".join(str(i)) for i in selected_titles_id))
    for search_title in search_titles:
        title_name = search_title["Title"]
        genre, created = Genre.objects.get_or_create(
            name=GENRE_ID[search_title["Cat"]])
        season = re.search(r"(\d+)", search_title["ShortTitle"])
        air_date = datetime.date(
            int(search_title["FirstYear"]), int(search_title["FirstMonth"]), 1)
        website = re.search(
            r'\[\[公式\s+(\S+)\]\]', search_title["Comment"])
        media_urls = re.findall(
            r'\[\[(|Twitter.*?|X.*?|YouTube.*?|ニコニコ.*?)\s+(\S+)\]\]', search_title["Comment"])
        tid = search_title["TID"]
        title_search = Title.objects.filter(title=search_title["Title"], season=int(
            season.group()) if season else 1)  # 同じのが登録されてないか探す
        if title_search.count() >= 1:
            messages.error(
                request, f"すでにタイトルが登録されているため追加しませんでした：{title_name}")
            continue
        elif title_search.count() == 0:
            title = Title(
                title=title_name,
                title_kana=search_title["TitleYomi"],
                content="\n".join(url for name, url in media_urls),
                genre=genre,
                season=int(season.group()) if season else 1,
                air_date=air_date,
                website=website.group(1) if website else "",
                source_website=f"https://cal.syoboi.jp/tid/{tid}"
            )
            titles.append(title)
    return titles


def process_syoboi_episodes(items, title, min_count: int, tid: str):
    title_episodes = Episode.objects.filter(
        title=title).order_by("episode_number")
    episodes = []
    update_episodes = []
    while True:
        for item in items:
            item_count = int(item.find("Count").text or 0)
            # 削除されているのと再放送は追加しない
            if min_count == item_count and int(item.find("Deleted").text) == 0 and int(item.find("Flag").text) != 8:
                start_time = datetime.datetime.strptime(
                    item.find("StTime").text, "%Y-%m-%d %H:%M:%S")
                end_time = datetime.datetime.strptime(
                    item.find("EdTime").text, "%Y-%m-%d %H:%M:%S")
                duration = end_time-start_time
                minutes = int(duration.total_seconds()//60)
                episode_number = int(item.find("Count").text)
                pid = item.find("PID").text
                episode_search = title_episodes.filter(
                    episode_number=episode_number)  # 同じのが登録されてないか探す
                if episode_search.count() >= 1 and episode_search.first().episode_title == "" and item.find("STSubTitle").text:
                    # 同じのが登録されていてエピソードタイトルが登録されていない場合登録する
                    episode = episode_search.first()
                    episode.episode_title = item.find("STSubTitle").text
                    episode.air_date = timezone.make_aware(start_time)
                    episode.source_website = f"https://cal.syoboi.jp/tid/{tid}/time#{pid}"
                    update_episodes.append(episode)
                elif episode_search.count() == 0:  # 何も登録されていない場合
                    episode = Episode(
                        title=title,
                        episode_title=item.find("STSubTitle").text or "",
                        episode_number=episode_number,
                        content="",
                        air_date=timezone.make_aware(start_time),
                        duration=minutes,
                        source_website=f"https://cal.syoboi.jp/tid/{tid}/time#{pid}"
                    )
                    episodes.append(episode)
                min_count = item_count+1
                break
        else:
            break
    return episodes, update_episodes, min_count


def parse_and_sort_program_items(root):
    items = sorted(root.findall(".//ProgItem"),
                   key=lambda x: int(x.find("TID").text))  # タイトルidで並べ替え
    items = sorted(root.findall(".//ProgItem"), key=lambda x: datetime.datetime.strptime(
        x.find("StTime").text, "%Y-%m-%d %H:%M:%S"))  # 放送開始時間順に並べ替え
    min_count = int(sorted(root.findall(".//ProgItem"), key=lambda x: int(
        x.find("Count").text or 999))[0].find("Count").text)  # 最小の回数を求める
    return items, min_count


def get_syoboi_calendar_episodes(title, selected_titles_id):

    tid = ",".join("".join(str(i)) for i in selected_titles_id)
    # for tid in selected_tid:
    try:
        r = requests.get(
            f"https://cal.syoboi.jp/db.php/db?Command=ProgLookup&TID={tid}&JOIN=SubTitles")
    except:
        return [], []
    if r.status_code != 200:
        return [], []
    root = ET.fromstring(r.text)
    items, min_count = parse_and_sort_program_items(root)
    episodes, update_episodes, min_count = process_syoboi_episodes(
        items, title, min_count, tid)
    return episodes, update_episodes


def create_and_update_episodes(episodes, update_episodes):
    Episode.objects.bulk_create(episodes)
    for episode in episodes:
        episode.tags.add(*episode.title.tags.all())
    if update_episodes:
        Episode.objects.bulk_update(
            update_episodes, ["episode_title", "air_date", "source_website"])


def get_program_items_by_pid(pid):
    try:
        r = requests.get(
            f"https://cal.syoboi.jp/db.php/db?Command=ProgLookup&PID={pid}&JOIN=SubTitles")
    except:
        return []
    if r.status_code != 200:
        return []
    root = ET.fromstring(r.text)
    items, min_count = parse_and_sort_program_items(root)
    return items


def auto_update_episodes(start_date: datetime.date = None, end_date: datetime.date = None):
    if not start_date:
        start_date = timezone.localtime(
            timezone.now()).date() - datetime.timedelta(days=1)  # 前日から
    if not end_date:
        end_date = start_date + datetime.timedelta(days=1)  # 翌日まで
    target_episodes = Episode.objects.filter(air_date__date__range=(
        start_date, end_date))
    if not target_episodes:
        return

    syoboi_episodes = []
    syoboi_items = []
    for episode in target_episodes:
        url = urlparse(episode.source_website)
        host_name = url.netloc
        if host_name == "cal.syoboi.jp":
            pid = url.fragment  # 最後の#からのpidを取り出す
            syoboi_episodes.append(
                {"pid": pid, "episode": episode, "title": episode.title})
    if syoboi_episodes:
        try:
            syoboi_items = get_program_items_by_pid(
                ",".join(str(i["pid"]) for i in syoboi_episodes))
        except:
            return
        if not syoboi_items:
            return
    for item in syoboi_items:
        title = next((p["title"] for p in syoboi_episodes if p["pid"] ==
                     item.find("PID").text), None)  # pidに対応するタイトルを取得
        episodes, update_episodes, min_count = process_syoboi_episodes(
            [item], title, int(item.find("Count").text), item.find("TID").text)
        create_and_update_episodes(episodes, update_episodes)
