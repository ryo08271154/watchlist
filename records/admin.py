from django.contrib import admin

from .models import WatchRecord, WatchMethod, EpisodeWatchRecord, MyList
admin.site.register(WatchRecord)
admin.site.register(WatchMethod)
admin.site.register(EpisodeWatchRecord)
admin.site.register(MyList)
