from django.contrib import admin
from .models import Genre,SubGenre,Title,Tag,Episode
# Register your models here.
class TitleAdmin(admin.ModelAdmin):
    list_display=("title","title_kana","genre","season","air_date")
class EpisodeAdmin(admin.ModelAdmin):
    list_display=("title","episode_title","episode_number","air_date")
admin.site.register(Genre)
admin.site.register(SubGenre)
admin.site.register(Title,TitleAdmin)
admin.site.register(Tag)
admin.site.register(Episode,EpisodeAdmin)
