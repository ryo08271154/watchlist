from django.urls import path
from . import views
app_name = "records"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("review/<uuid:pk>", views.ReviewDetailView.as_view(), name="review_detail"),
    path("reviews/import", views.ReviewImportView.as_view(), name="review_import"),
    path("title/<uuid:pk>/review", views.TitleReviewListView.as_view(),
         name="title_review_list"),
    path("title/<uuid:pk>/review/new",
         views.ReviewCreateView.as_view(), name="title_review_create"),
    path("review/<uuid:pk>/edit", views.ReviewEditView.as_view(), name="review_edit"),
    path("episode/<uuid:pk>/review",
         views.EpisodeReviewListView.as_view(), name="episode_review_list"),
    path("episode/<uuid:pk>/review/new",
         views.EpisodeCreateView.as_view(), name="episode_review_create"),
    path("episode_review/<uuid:pk>",
         views.EpisodeReviewDetailView.as_view(), name="episode_review_detail"),
    path("episode_review/<uuid:pk>/edit",
         views.EpisodeReviewEditView.as_view(), name="episode_review_edit"),

    path("mylist", views.MyListView.as_view(), name="mylist"),
    path("mylist/new", views.MyListCreateView.as_view(), name="mylist_create"),
    path("mylist/<uuid:pk>/edit", views.MyListEditView.as_view(), name="mylist_edit"),
    path("mylist/<uuid:pk>", views.MyListDetailView.as_view(), name="mylist_detail"),
    path("title/<uuid:pk>/add_mylist", views.MyListAddTitleView.as_view(),
         name="add_mylist"),


    path("tags/", views.TagView.as_view(), name="tag_list"),
    path("tag/<uuid:pk>", views.TagDetailView.as_view(), name="tag_detail"),

    path("search", views.SearchView.as_view(), name="search"),

    path("mypage", views.MypageView.as_view(), name="mypage"),
    path("mypage/reviews", views.MyReviewListView.as_view(), name="myreview"),
    path("mypage/stats", views.MyStatsView.as_view(), name="mystats"),

    path("export", views.ExportView.as_view(), name="export"),
    path("export/reviews", views.ReviewExportView.as_view(), name="review_export"),
    path("export/episode_reviews", views.EpisodeReviewExportView.as_view(),
         name="episode_review_export"),
    path("export/mylists", views.MyListExportView.as_view(), name="mylist_export"),


    path("share", views.AddFromShareView.as_view(), name="add_from_share"),
]
