from django.urls import path
from . import views

app_name = 'authentication_api'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('activate/<str:uidb64>/<str:token>/', views.activate_view, name='activate'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', views.refresh_token_view, name='token_refresh'),
]