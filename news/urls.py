from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='list'),
    path('<int:news_id>/', views.news_detail, name='detail'),
    path('create/', views.news_create, name='create'),
    path('<int:news_id>/edit/', views.news_edit, name='edit'),
]