from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.class_chat_list, name='class_list'),
    path('<int:class_id>/', views.class_chat_detail, name='class_detail'),
    path('api/<int:class_id>/messages/', views.get_new_messages, name='get_messages'),
    path('file/<int:message_id>/', views.get_file, name='get_file'),
]