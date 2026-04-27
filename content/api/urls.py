from django.urls import path
from . import views

app_name = 'content_api'

urlpatterns = [
    path('video/', views.video_list_view, name='video_list'),
    path('video/<int:pk>/', views.video_detail_view, name='video_detail'),
    path('video/<int:movie_id>/master.m3u8', views.video_hls_master_playlist_view, name='video_hls_master_playlist'),
    path('video/<int:movie_id>/<str:resolution>/index.m3u8', views.video_hls_playlist_view, name='video_hls_playlist'),
    path('video/<int:movie_id>/<str:resolution>/<str:segment>/', views.video_hls_segment_view, name='video_hls_segment'),
]