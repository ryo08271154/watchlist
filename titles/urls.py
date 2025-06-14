from django.urls import path
from . import views
app_name="titles"
urlpatterns=[path("titles/",views.TitleListView.as_view(),name="title_list"),
             path("title/<uuid:pk>",views.TitleDetailView.as_view(),name="title_detail"),
             path("title/<uuid:pk>/edit",views.TitleEditView.as_view(),name="title_edit"),
             path("title/new",views.TitleCreateView.as_view(),name="title_create"),
             path("titles/import",views.TitleImportView.as_view(),name="title_import"),
             path("titles/import/external",views.TitleSourceImportView.as_view(),name="title_import_external"),

             path("title/<uuid:pk>/episodes",views.TitleEpisodeView.as_view(),name="title_episodes"),
             path("title/<uuid:pk>/episode/new",views.TitleEpisodeCreateView.as_view(),name="title_episode_create"),
             path("title/<uuid:pk>/episode/import",views.EpisodeImportView.as_view(),name="episode_import"),
             path("title/<uuid:pk>/episode/import/external",views.TitleEpisodeSourceImportView.as_view(),name="title_episode_import_external"),
             path("episode/<uuid:pk>",views.EpisodeDetailView.as_view(),name="episode_detail"),
             path("episode/<uuid:pk>/edit",views.EpisodeEditView.as_view(),name="episode_edit"),
             path("watch_schedule",views.MyWatchScheduleView.as_view(),name="watch_schedule"),

            path("titles/export",views.TitleExportView.as_view(),name="title_export"),
            path("episodes/export",views.EpisodeExportView.as_view(),name="episode_export")
            ]