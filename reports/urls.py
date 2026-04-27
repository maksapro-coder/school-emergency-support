from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Отчет по посещаемости
    path('attendance/', views.attendance_report, name='attendance_report'),
    path('attendance/export/pdf/', views.export_attendance_pdf, name='export_attendance_pdf'),
    path('attendance/export/excel/', views.export_attendance_excel, name='export_attendance_excel'),
    
    # Отчет по успеваемости
    path('progress/', views.progress_report, name='progress_report'),
    path('progress/export/pdf/', views.export_progress_pdf, name='export_progress_pdf'),
    path('progress/export/excel/', views.export_progress_excel, name='export_progress_excel'),
]