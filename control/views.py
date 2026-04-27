from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime

from .models import Attendance, Grade, Homework, HomeworkSubmission
from classes.models import Lesson
from administration.models import Class as SchoolClass

@login_required
def attendance_list(request):
    """Список посещаемости"""
    if request.user.is_teacher() or request.user.is_admin():
        # Для учителя показываем посещаемость всех уроков, которые он ведет
        if request.user.is_teacher():
            attendances = Attendance.objects.filter(lesson__teacher=request.user).select_related(
                'lesson', 'lesson__subject', 'student', 'marked_by'
            ).order_by('-lesson__date', '-lesson__start_time')
        else:
            # Для админа показываем всю посещаемость
            attendances = Attendance.objects.all().select_related(
                'lesson', 'lesson__subject', 'student', 'marked_by'
            ).order_by('-lesson__date', '-lesson__start_time')
    else:
        # Для учеников показываем только их посещаемость
        attendances = Attendance.objects.filter(
            student=request.user
        ).select_related('lesson', 'lesson__subject').order_by('-lesson__date', '-lesson__start_time')
    
    return render(request, 'control/attendance_list.html', {'attendances': attendances})

@login_required
def mark_attendance(request, lesson_id):
    """Отметка посещаемости (для учителя)"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'У вас нет прав для отметки посещаемости')
        return redirect('users:dashboard')
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверяем, имеет ли учитель право отмечать посещаемость для этого урока
    if request.user.is_teacher() and lesson.teacher != request.user:
        messages.error(request, 'Вы не являетесь преподавателем этого урока')
        return redirect('classes:lesson_detail', lesson_id=lesson.id)
    
    # Получаем список учеников класса
    students = lesson.class_group.students.select_related('student').all()
    students_list = [sc.student for sc in students]
    
    if request.method == 'POST':
        # Обрабатываем отметку посещаемости
        for student in students_list:
            status = request.POST.get(f'status_{student.id}')
            note = request.POST.get(f'note_{student.id}', '')
            
            if status:
                Attendance.objects.update_or_create(
                    lesson=lesson,
                    student=student,
                    defaults={
                        'status': status,
                        'marked_by': request.user,
                        'notes': note
                    }
                )
        
        messages.success(request, 'Посещаемость успешно отмечена')
        return redirect('classes:lesson_detail', lesson_id=lesson.id)
    
    # Получаем уже отмеченную посещаемость для предзаполнения формы
    existing_attendance = {
        a.student_id: a for a in Attendance.objects.filter(lesson=lesson)
    }
    
    return render(request, 'control/mark_attendance.html', {
        'lesson': lesson,
        'students': students_list,
        'existing_attendance': existing_attendance
    })

@login_required
def grade_list(request):
    """Список оценок"""
    if request.user.is_teacher() or request.user.is_admin():
        # Для учителя показываем оценки, которые он выставил
        if request.user.is_teacher():
            grades = Grade.objects.filter(teacher=request.user).select_related(
                'student', 'lesson', 'lesson__subject'
            ).order_by('-date')
        else:
            # Для админа показываем все оценки
            grades = Grade.objects.all().select_related(
                'student', 'teacher', 'lesson', 'lesson__subject'
            ).order_by('-date')
    else:
        # Для учеников показываем только их оценки
        grades = Grade.objects.filter(
            student=request.user
        ).select_related('lesson', 'lesson__subject', 'teacher').order_by('-date')
    
    return render(request, 'control/grade_list.html', {'grades': grades})

@login_required
def add_grade(request, lesson_id):
    """Выставление оценки (для учителя)"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'У вас нет прав для выставления оценок')
        return redirect('users:dashboard')
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    
    # Проверяем, имеет ли учитель право выставлять оценки для этого урока
    if request.user.is_teacher() and lesson.teacher != request.user:
        messages.error(request, 'Вы не являетесь преподавателем этого урока')
        return redirect('classes:lesson_detail', lesson_id=lesson.id)
    
    # Получаем список учеников класса
    students = lesson.class_group.students.select_related('student').all()
    students_list = [sc.student for sc in students]
    
    if request.method == 'POST':
        # Обрабатываем выставление оценок
        for student in students_list:
            grade_value = request.POST.get(f'grade_{student.id}')
            grade_type = request.POST.get(f'grade_type_{student.id}', 'current')
            comment = request.POST.get(f'comment_{student.id}', '')
            
            if grade_value and grade_value.strip():
                Grade.objects.create(
                    student=student,
                    lesson=lesson,
                    subject=lesson.subject.name,
                    grade=int(grade_value),
                    grade_type=grade_type,
                    teacher=request.user,
                    comment=comment
                )
        
        messages.success(request, 'Оценки успешно выставлены')
        return redirect('classes:lesson_detail', lesson_id=lesson.id)
    
    # Получаем уже выставленные оценки для предзаполнения формы
    existing_grades = {
        g.student_id: g for g in Grade.objects.filter(lesson=lesson)
    }
    
    return render(request, 'control/add_grade.html', {
        'lesson': lesson,
        'students': students_list,
        'existing_grades': existing_grades
    })

@login_required
def homework_list(request):
    """Список домашних заданий"""
    if request.user.is_teacher() or request.user.is_admin():
        # Для учителя показываем все задания, которые он создал
        if request.user.is_teacher():
            homeworks = Homework.objects.filter(created_by=request.user).select_related(
                'lesson', 'lesson__subject', 'lesson__class_group', 'created_by'
            ).prefetch_related('submissions').order_by('-due_date')
        else:
            # Для админа показываем все задания
            homeworks = Homework.objects.all().select_related(
                'lesson', 'lesson__subject', 'lesson__class_group', 'created_by'
            ).prefetch_related('submissions').order_by('-due_date')
    else:
        # Для учеников показываем задания их класса
        student_classes = request.user.student_classes.select_related('class_group').all()
        class_ids = [sc.class_group.id for sc in student_classes]
        
        homeworks = Homework.objects.filter(
            lesson__class_group_id__in=class_ids
        ).select_related(
            'lesson', 'lesson__subject', 'created_by'
        ).prefetch_related(
            'submissions'
        ).order_by('-due_date')
    
    return render(request, 'control/homework_list.html', {'homeworks': homeworks})

@login_required
def add_homework(request):
    """Добавление домашнего задания (для учителя)"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'У вас нет прав для добавления заданий')
        return redirect('users:dashboard')
    
    # Получаем уроки, которые ведет учитель
    if request.user.is_teacher():
        lessons = Lesson.objects.filter(
            teacher=request.user,
            date__gte=timezone.now().date()
        ).select_related('subject', 'class_group').order_by('date', 'start_time')
    else:
        # Для админа показываем все будущие уроки
        lessons = Lesson.objects.filter(
            date__gte=timezone.now().date()
        ).select_related('subject', 'class_group', 'teacher').order_by('date', 'start_time')
    
    if request.method == 'POST':
        lesson_id = request.POST.get('lesson')
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        
        lesson = get_object_or_404(Lesson, id=lesson_id)
        
        homework = Homework.objects.create(
            lesson=lesson,
            title=title,
            description=description,
            due_date=due_date,
            created_by=request.user
        )
        
        # Обработка загруженного файла
        if 'attachments' in request.FILES:
            homework.attachments = request.FILES['attachments']
            homework.save()
        
        messages.success(request, f'Домашнее задание "{title}" успешно создано')
        return redirect('control:homework_list')
    
    return render(request, 'control/add_homework.html', {'lessons': lessons})

@login_required
def homework_detail(request, homework_id):
    """Детальная информация о домашнем задании"""
    homework = get_object_or_404(
        Homework.objects.select_related('lesson', 'lesson__subject', 'lesson__class_group', 'created_by'),
        id=homework_id
    )
    
    # Проверка доступа для ученика
    if request.user.is_student():
        student_classes = request.user.student_classes.filter(class_group=homework.lesson.class_group)
        if not student_classes.exists():
            messages.error(request, 'У вас нет доступа к этому заданию')
            return redirect('control:homework_list')
    
    return render(request, 'control/homework_detail.html', {'homework': homework})

@login_required
def submit_homework(request, homework_id):
    """Сдача домашнего задания (для ученика)"""
    if not request.user.is_student():
        messages.error(request, 'Только ученики могут сдавать задания')
        return redirect('users:dashboard')
    
    homework = get_object_or_404(Homework, id=homework_id)
    
    # Проверяем, учится ли ученик в классе, для которого задано задание
    if not request.user.student_classes.filter(class_group=homework.lesson.class_group).exists():
        messages.error(request, 'У вас нет доступа к этому заданию')
        return redirect('control:homework_list')
    
    # Проверяем, не сдавал ли ученик уже это задание
    existing_submission = HomeworkSubmission.objects.filter(
        homework=homework,
        student=request.user
    ).first()
    
    if existing_submission:
        messages.error(request, 'Вы уже сдали это задание')
        return redirect('control:homework_detail', homework_id=homework.id)
    
    if request.method == 'POST':
        comment = request.POST.get('comment', '')
        submission_file = request.FILES.get('submission_file')
        
        if not submission_file:
            messages.error(request, 'Выберите файл для загрузки')
            return render(request, 'control/submit_homework.html', {'homework': homework})
        
        HomeworkSubmission.objects.create(
            homework=homework,
            student=request.user,
            submission_file=submission_file,
            comment=comment
        )
        
        messages.success(request, 'Задание успешно сдано')
        return redirect('control:homework_detail', homework_id=homework.id)
    
    return render(request, 'control/submit_homework.html', {'homework': homework})

@login_required
def grade_submission(request, submission_id):
    """Оценка сданного задания (для учителя)"""
    if not request.user.is_teacher() and not request.user.is_admin():
        messages.error(request, 'У вас нет прав для оценки заданий')
        return redirect('users:dashboard')
    
    submission = get_object_or_404(
        HomeworkSubmission.objects.select_related('homework', 'homework__lesson', 'student'),
        id=submission_id
    )
    
    # Проверяем, имеет ли учитель право оценивать это задание
    if request.user.is_teacher() and submission.homework.lesson.teacher != request.user:
        messages.error(request, 'Вы не являетесь преподавателем этого предмета')
        return redirect('control:homework_list')
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        feedback = request.POST.get('feedback', '')
        
        if grade:
            submission.grade = int(grade)
            submission.feedback = feedback
            submission.save()
            
            messages.success(request, f'Оценка выставлена: {grade}')
        else:
            messages.error(request, 'Укажите оценку')
        
        return redirect('control:homework_detail', homework_id=submission.homework.id)
    
    return render(request, 'control/grade_submission.html', {'submission': submission})