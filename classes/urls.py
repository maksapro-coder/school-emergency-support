from django.urls import path
from . import views

app_name = 'classes'

urlpatterns = [
    path('', views.class_list, name='class_list'),
    path('<int:class_id>/', views.class_detail, name='class_detail'),
    path('<int:class_id>/schedule/', views.class_schedule, name='class_schedule'),
    path('<int:class_id>/create-lesson/', views.create_lesson, name='create_lesson'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/join/', views.join_lesson, name='join_lesson'),
]