from django.urls import path
from . import views

app_name = 'control'

urlpatterns = [
    # Посещаемость
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance/mark/<int:lesson_id>/', views.mark_attendance, name='mark_attendance'),
    
    # Оценки
    path('grades/', views.grade_list, name='grade_list'),
    path('grades/add/<int:lesson_id>/', views.add_grade, name='add_grade'),
    
    # Домашние задания
    path('homework/', views.homework_list, name='homework_list'),
    path('homework/add/', views.add_homework, name='add_homework'),
    path('homework/<int:homework_id>/submit/', views.submit_homework, name='submit_homework'),
]