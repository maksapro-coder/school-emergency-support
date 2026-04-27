from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages  # Добавлен импорт messages
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta

from administration.models import Class as SchoolClass, Subject
from .models import Lesson
from users.models import User

@login_required
def class_list(request):
    """Список классов (для учителей и администраторов)"""
    if request.user.is_teacher() or request.user.is_admin():
        classes = SchoolClass.objects.all()  # Используем SchoolClass
        return render(request, 'classes/class_list.html', {'classes': classes})
    else:
        # Для учеников показываем только их класс
        student_class = request.user.student_classes.first()
        if student_class:
            return redirect('classes:class_detail', class_id=student_class.class_group.id)
        else:
            return render(request, 'classes/no_class.html')

@login_required
def class_detail(request, class_id):
    """Детальная информация о классе"""
    class_group = get_object_or_404(SchoolClass, id=class_id)  # Используем SchoolClass
    students = class_group.students.all()
    return render(request, 'classes/class_detail.html', {
        'class_group': class_group,
        'students': students
    })

@login_required
def class_schedule(request, class_id):
    """Расписание для класса"""
    class_group = get_object_or_404(SchoolClass, id=class_id)  # Используем SchoolClass
    lessons = Lesson.objects.filter(class_group=class_group).order_by('date', 'start_time')
    return render(request, 'classes/class_schedule.html', {
        'class_group': class_group,
        'lessons': lessons
    })

@login_required
def lesson_detail(request, lesson_id):
    """Детальная информация об уроке"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    return render(request, 'classes/lesson_detail.html', {'lesson': lesson})

@login_required
def join_lesson(request, lesson_id):
    """Подключение к онлайн-уроку"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверяем, имеет ли пользователь доступ к уроку
    if request.user.is_student():
        # Проверяем, учится ли ученик в этом классе
        if not request.user.student_classes.filter(class_group=lesson.class_group).exists():
            messages.error(request, 'У вас нет доступа к этому уроку')
            return redirect('classes:class_list')
    elif request.user.is_teacher():
        # Проверяем, является ли учитель преподавателем этого урока
        if lesson.teacher != request.user:
            messages.error(request, 'Вы не являетесь преподавателем этого урока')
            return redirect('classes:class_list')
    elif not request.user.is_admin():
        # Если не ученик, не учитель и не админ
        messages.error(request, 'У вас нет доступа к этому уроку')
        return redirect('users:dashboard')
    
    # Активируем урок, если он еще не активен
    if not lesson.is_active:
        lesson.is_active = True
        lesson.save()
    
    return render(request, 'classes/join_lesson.html', {'lesson': lesson})

@login_required
def create_lesson(request, class_id):
    """Создание нового урока (для учителя)"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'У вас нет прав для создания уроков')
        return redirect('users:dashboard')
    
    class_group = get_object_or_404(SchoolClass, id=class_id)
    subjects = Subject.objects.all()
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        topic = request.POST.get('topic')
        description = request.POST.get('description')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        subject = get_object_or_404(Subject, id=subject_id)
        
        lesson = Lesson.objects.create(
            class_group=class_group,
            subject=subject,
            teacher=request.user if request.user.is_teacher() else None,
            topic=topic,
            description=description,
            date=date,
            start_time=start_time,
            end_time=end_time
        )
        
        messages.success(request, f'Урок "{topic}" успешно создан')
        return redirect('classes:class_schedule', class_id=class_group.id)
    
    # Предлагаем следующую дату для урока
    tomorrow = timezone.now().date() + timedelta(days=1)
    
    return render(request, 'classes/create_lesson.html', {
        'class_group': class_group,
        'subjects': subjects,
        'tomorrow': tomorrow.isoformat()
    })