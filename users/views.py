from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Avg, Count
from django.utils import timezone
from datetime import timedelta

from .models import User
from administration.models import School, Class as SchoolClass  # Добавлен SchoolClass
from classes.models import Lesson
from control.models import Grade, Attendance, Homework, HomeworkSubmission

@login_required
def dashboard(request):
    """Главная страница в зависимости от роли пользователя"""
    user = request.user
    school = School.objects.first()
    
    if user.is_teacher():
        # Статистика для учителя
        my_lessons = Lesson.objects.filter(teacher=user)
        total_lessons = my_lessons.count()
        
        # Мои классы
        my_classes = SchoolClass.objects.filter(
            lessons__teacher=user
        ).distinct()
        
        # Ученики
        total_students = User.objects.filter(
            role='student',
            student_classes__class_group__in=my_classes
        ).distinct().count()
        
        # Средний балл
        avg_grade = Grade.objects.filter(
            teacher=user
        ).aggregate(Avg('grade'))['grade__avg'] or 0
        
        # Посещаемость
        total_attendances = Attendance.objects.filter(
            lesson__teacher=user
        ).count()
        present_attendances = Attendance.objects.filter(
            lesson__teacher=user,
            status='present'
        ).count()
        attendance_rate = round(present_attendances / total_attendances * 100) if total_attendances > 0 else 0
        
        # Ближайшие уроки
        upcoming_lessons = my_lessons.filter(
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')[:5]
        
        # Непроверенные работы
        pending_homeworks = HomeworkSubmission.objects.filter(
            homework__lesson__teacher=user,
            grade__isnull=True
        ).select_related('student', 'homework')[:5]
        
        context = {
            'school': school,
            'total_lessons': total_lessons,
            'my_classes': my_classes,
            'total_students': total_students,
            'avg_grade': avg_grade,
            'attendance_rate': attendance_rate,
            'upcoming_lessons': upcoming_lessons,
            'pending_homeworks': pending_homeworks,
        }
        return render(request, 'users/teacher_dashboard.html', context)
    
    elif user.is_student():
        # Статистика для ученика
        # Мои классы - используем импортированный SchoolClass
        my_classes = SchoolClass.objects.filter(
            students__student=user
        )
        
        # Мои оценки
        my_grades = Grade.objects.filter(student=user)
        avg_grade = my_grades.aggregate(Avg('grade'))['grade__avg'] or 0
        
        # Посещаемость
        my_attendances = Attendance.objects.filter(student=user)
        total = my_attendances.count()
        present = my_attendances.filter(status='present').count()
        attendance_rate = round(present / total * 100) if total > 0 else 0
        
        # Ближайшие уроки
        upcoming_lessons = Lesson.objects.filter(
            class_group__in=my_classes,
            date__gte=timezone.now().date()
        ).order_by('date', 'start_time')[:5]
        
        # Активные домашние задания
        active_homeworks = Homework.objects.filter(
            lesson__class_group__in=my_classes,
            due_date__gte=timezone.now()
        ).exclude(
            submissions__student=user
        ).select_related('lesson', 'lesson__subject')[:5]
        
        context = {
            'school': school,
            'my_classes': my_classes,
            'my_grades': my_grades[:5],
            'avg_grade': avg_grade,
            'attendance_rate': attendance_rate,
            'upcoming_lessons': upcoming_lessons,
            'active_homeworks': active_homeworks,
        }
        return render(request, 'users/student_dashboard.html', context)
    
    else:  # admin
        # Статистика для админа
        total_users = User.objects.count()
        total_teachers = User.objects.filter(role='teacher').count()
        total_students = User.objects.filter(role='student').count()
        total_classes = SchoolClass.objects.count()
        total_lessons = Lesson.objects.count()
        
        # Активность за последние 7 дней
        last_week = timezone.now().date() - timedelta(days=7)
        
        recent_attendances = Attendance.objects.filter(
            lesson__date__gte=last_week
        ).count()
        
        recent_grades = Grade.objects.filter(
            date__gte=last_week
        ).count()
        
        context = {
            'school': school,
            'total_users': total_users,
            'total_teachers': total_teachers,
            'total_students': total_students,
            'total_classes': total_classes,
            'total_lessons': total_lessons,
            'recent_attendances': recent_attendances,
            'recent_grades': recent_grades,
        }
        return render(request, 'users/admin_dashboard.html', context)

@login_required
def profile(request):
    """Просмотр профиля"""
    return render(request, 'users/profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    """Редактирование профиля"""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.patronymic = request.POST.get('patronymic', user.patronymic)
        user.phone = request.POST.get('phone', user.phone)
        user.email = request.POST.get('email', user.email)
        
        if 'avatar' in request.FILES:
            user.avatar = request.FILES['avatar']
        
        # Проверка и обновление пароля
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        if new_password and new_password == confirm_password:
            user.set_password(new_password)
            update_session_auth_hash(request, user)
            messages.success(request, 'Пароль успешно изменен')
        
        user.save()
        messages.success(request, 'Профиль успешно обновлен')
        return redirect('users:profile')
    
    return render(request, 'users/edit_profile.html', {'user': request.user})

def handler404(request, exception):
    """Обработчик ошибки 404"""
    return render(request, '404.html', status=404)

def handler500(request):
    """Обработчик ошибки 500"""
    return render(request, '500.html', status=500)