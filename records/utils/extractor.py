from ..models import Title, Episode
from django.db.models import Exists, OuterRef, Q, Max

import re
import unicodedata
from typing import Optional, List


class Extractor:
    EXCLUDED_WORDS = [
        "ビデオ",
        "TV",
        "テレビ",
        "映画",
        "番組",
        "アニメ",
        "漫画",
        "漫画",
        "ゲーム",
        "音楽",
        "書籍",
        "本",
        "作品",
        "無料",
        "人気",
        "No",
        "動画",
        "配信",
        "最新話",
        "公式",
        "あらすじ",
        "感想",
        "まとめ",
        "サイト",
        "ページ",
        "円",
        "レビュー",
        "字幕",
        "吹き替え",
        "見放題",
        "検索",
        "おすすめ",
        "独占",
        "ランキング",
        "履歴",
        "購入",
        "マイリスト",
        "マイページ",
        "設定",
        "アカウント",
        "ログイン",
        "ログアウト",
        "詳細",
        "情報",
        "お知らせ",
        "ニュース",
        "メッセージ",
    ]

    def _normalize_text(self, text: str) -> str:
        normalized = unicodedata.normalize('NFKC', text)
        normalized = re.sub(
            r'[,\.~!@#\$%\^&\*_\+\-=\{\}\[\]:;"\'<>?\\\/\|]', " ", normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        return normalized

    def split_into_words(self, text: str) -> List[str]:
        normalized = self._normalize_text(text)
        words = re.split(r"[ 　\|｜{}【】（）()*~・「」『』《》<>、。・@＠をでに]", normalized)
        return [word for word in words if word]

    def _should_skip_word(self, word: str) -> bool:
        if len(word) <= 3:
            return True
        for excluded in self.EXCLUDED_WORDS:
            if excluded in word:
                return True
        return False

    def get_episode_number(self, text: str) -> int:
        pattern = r"(Episode|エピソード|#|＃|EP)(\d+)|(\d+)(話)"
        match = re.search(pattern, text)
        if match:
            episode_number = int(
                match.group(2) if match.group(2) else match.group(3)
            )
            return episode_number
        return 0

    def match_from_keywords(self, obj, field: str, keywords: List[str], filter=None, check_episode=False) -> bool:
        episode_number = self.get_episode_number(" ".join(keywords))
        for keyword in keywords:
            if self._should_skip_word(keyword):
                continue

            filter_kwargs = {f"{field}__icontains": keyword}
            matched = obj.objects.filter(**filter_kwargs)
            if matched and filter:
                matched = matched.filter(filter)
            if matched.count() > 8:
                continue
            if check_episode and episode_number != 0:
                # エピソードが存在するか確認
                episode = Episode.objects.filter(
                    title__in=matched, episode_number=episode_number)
                if episode.exists():
                    return episode.first().title
            else:
                if matched:
                    return matched.first()


class TitleExtractor(Extractor):
    def extract_title(self, title: str, text: str):
        keywords = [
            *self.split_into_words(title), *self.split_into_words(text)]
        matched_title = self.match_from_keywords(
            Title, "title", keywords, check_episode=True)
        return matched_title


class EpisodeExtractor(Extractor):
    def extract_episode(self, title_obj: Title, title: str, text: str):
        title_filter = Q(title=title_obj) | Q(
            title__in=title_obj.related_titles.all())

        episode_number = self.get_episode_number(f"{title} {text}")
        if episode_number:
            return Episode.objects.filter(title_filter, episode_number=episode_number).first()

        keywords = [
            *self.split_into_words(title), *self.split_into_words(text)]
        matched_episode = self.match_from_keywords(
            Episode, "episode_title", keywords, filter=title_filter)
        return matched_episode
