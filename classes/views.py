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
    if request.user.is_teacher():
        from administration.models import ClassTeacher, ClassSubjectTeacher
        
        # Получаем классы, где учитель является классным руководителем
        managed_classes = ClassTeacher.objects.filter(
            teacher=request.user
        ).values_list('class_group_id', flat=True)
        
        # Получаем классы, где учитель ведет предметы
        taught_classes = ClassSubjectTeacher.objects.filter(
            teacher=request.user
        ).values_list('class_group_id', flat=True)
        
        # Объединяем и получаем уникальные классы
        class_ids = set(list(managed_classes) + list(taught_classes))
        classes = SchoolClass.objects.filter(id__in=class_ids)
        
        return render(request, 'classes/class_list.html', {'classes': classes})
    
    elif request.user.is_admin():
        classes = SchoolClass.objects.all()
        return render(request, 'classes/class_list.html', {'classes': classes})
    
    else:
        # Для учеников показываем только их класс
        student_class = request.user.student_classes.first()
        if student_class:
            return redirect('classes:class_detail', class_id=student_class.class_group.id)
        else:
            return render(request, 'classes/no_class.html')

@login_required
def activate_lesson(request, lesson_id):
    """Активация урока (только для учителя)"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if not request.user.is_teacher() or lesson.teacher != request.user:
        messages.error(request, 'У вас нет прав для активации этого урока')
        return redirect('classes:class_schedule', class_id=lesson.class_group.id)
    
    lesson.is_active = True
    lesson.save()
    
    messages.success(request, f'Урок "{lesson.topic}" активирован. Ученики могут подключаться.')
    return redirect('classes:class_schedule', class_id=lesson.class_group.id)


@login_required
def end_lesson(request, lesson_id):
    """Завершение урока (только для учителя)"""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    if not request.user.is_teacher() or lesson.teacher != request.user:
        messages.error(request, 'У вас нет прав для завершения этого урока')
        return redirect('classes:class_schedule', class_id=lesson.class_group.id)
    
    lesson.is_active = False
    lesson.save()
    
    messages.success(request, f'Урок "{lesson.topic}" завершен.')
    return redirect('classes:class_schedule', class_id=lesson.class_group.id)


@login_required
def class_detail(request, class_id):
    """Детальная информация о классе"""
    class_group = get_object_or_404(SchoolClass, id=class_id)
    students = class_group.students.select_related('student').all()
    
    return render(request, 'classes/class_detail.html', {
        'class_group': class_group,
        'students': students,  # Передаём список объектов StudentClass
    })

@login_required
@login_required
def class_schedule(request, class_id):
    """Расписание для класса"""
    try:
        class_group = get_object_or_404(SchoolClass, id=class_id)
        lessons = Lesson.objects.filter(class_group=class_group).order_by('date', 'start_time')
        
        # Добавим отладочный вывод в консоль
        print(f"DEBUG: class_schedule - class_id: {class_id}")
        print(f"DEBUG: Найдено уроков: {lessons.count()}")
        for lesson in lessons:
            print(f"DEBUG: Урок {lesson.id}: {lesson.topic}")
        
        return render(request, 'classes/class_schedule.html', {
            'class_group': class_group,
            'lessons': lessons
        })
    except Exception as e:
        print(f"ERROR in class_schedule: {e}")
        # Временный ответ для отладки
        return HttpResponse(f"Ошибка: {e}")

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