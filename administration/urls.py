from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    # Школа
    path('school/', views.school_settings, name='school_settings'),
    
    # Классы
    path('classes/', views.admin_class_list, name='admin_class_list'),
    path('classes/create/', views.create_class, name='create_class'),
    path('classes/<int:class_id>/edit/', views.edit_class, name='edit_class'),
    path('classes/<int:class_id>/students/', views.class_students, name='class_students'),
    
    # Предметы
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/<int:subject_id>/edit/', views.edit_subject, name='edit_subject'),
    path('subjects/<int:subject_id>/delete/', views.delete_subject, name='delete_subject'),
    
    # Пользователи
    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Настройки ЧС
    path('emergency/', views.emergency_settings, name='emergency_settings'),
    path('emergency/activate/', views.activate_emergency, name='activate_emergency'),
]