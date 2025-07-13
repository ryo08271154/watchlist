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
                embed_html.append(f'<iframe width="300" height="200" src="https://www.youtube.com/embed/{video_id}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>')
            elif playlist_id:
                embed_html.append(f'<iframe width="300" height="200" src="https://www.youtube.com/embed/videoseries?list={playlist_id}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>')
    return embed_html