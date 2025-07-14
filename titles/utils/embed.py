import re
def generate_embed_html(text) -> list:
    urls = re.findall(r"https?://[\w/:%#$&?()~.=+-]+", text)
    if not urls:
        return ""
    embed_html = []
    for url in urls:
        video_id = None
        playlist_id = None
        if "youtube.com/" in url or "youtu.be/" in url:
            if "youtube.com/watch?v=" in url:
                video_id = url.split("?v=")[1][:12] #動画idは必ず11桁
            elif "youtu.be/" in url:
                video_id = url.split("/")[3][:12]
            elif "youtube.com/playlist?list=" in url:
                playlist_id = url.split("?list=")[1]
            if video_id:
                embed_html.append(f'<iframe width="320" height="180" src="https://www.youtube.com/embed/{video_id}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>')
            elif playlist_id:
                embed_html.append(f'<iframe width="320" height="180" src="https://www.youtube.com/embed/videoseries?list={playlist_id}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>')
        if "nicovideo.jp/" in url:
            if "nicovideo.jp/watch/" in url:
                video_id = url.split("/")[4]
                embed_html.append(f'<script type="application/javascript" src="https://embed.nicovideo.jp/watch/{video_id}/script?w=320&h=180"></script><noscript><a href="https://www.nicovideo.jp/watch/{video_id}">https://www.nicovideo.jp/watch/{video_id}</a></noscript>')
            if "ch.nicovideo.jp/" in url:
                channel_id = url.split("/")[3]
                embed_html.append(f'<iframe src="https://ch.nicovideo.jp/{channel_id}/thumb_channel" width="312" height="176" frameborder="0" scrolling="no"></iframe>')
    return embed_html