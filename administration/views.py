from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from datetime import datetime

from .models import School, Class, StudentClass, ClassTeacher, Subject, ClassSubjectTeacher
from users.models import User

@login_required
def school_settings(request):
    """Настройки школы (только для администратора)"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    school = School.objects.first()
    
    if request.method == 'POST':
        if school:
            # Обновляем существующую школу
            school.name = request.POST.get('name')
            school.address = request.POST.get('address')
            school.phone = request.POST.get('phone')
            school.email = request.POST.get('email')
            school.director_name = request.POST.get('director_name')
            school.save()
            messages.success(request, 'Настройки школы успешно обновлены')
        else:
            # Создаем новую школу
            school = School.objects.create(
                name=request.POST.get('name'),
                address=request.POST.get('address'),
                phone=request.POST.get('phone'),
                email=request.POST.get('email'),
                director_name=request.POST.get('director_name')
            )
            messages.success(request, 'Школа успешно создана')
        return redirect('administration:school_settings')
    
    return render(request, 'administration/school_settings.html', {'school': school})

@login_required
def class_teachers(request, class_id):
    """Управление преподавателями в классе"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    class_group = get_object_or_404(Class, id=class_id)
    all_teachers = User.objects.filter(role='teacher').order_by('last_name', 'first_name')
    subjects = Subject.objects.all().order_by('name')
    
    # Обработка POST запроса
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_class_teacher':
            teacher_id = request.POST.get('teacher_id')
            if teacher_id:
                teacher = get_object_or_404(User, id=teacher_id, role='teacher')
                ClassTeacher.objects.get_or_create(
                    class_group=class_group,
                    teacher=teacher,
                    academic_year=class_group.academic_year
                )
                messages.success(request, f'Учитель {teacher.get_full_name()} назначен классным руководителем')
        
        elif action == 'remove_class_teacher':
            teacher_id = request.POST.get('teacher_id')
            if teacher_id:
                ClassTeacher.objects.filter(
                    class_group=class_group,
                    teacher_id=teacher_id,
                    academic_year=class_group.academic_year
                ).delete()
                messages.success(request, 'Классный руководитель удален')
        
        elif action == 'add_subject_teacher':
            teacher_id = request.POST.get('teacher_id')
            subject_id = request.POST.get('subject_id')
            if teacher_id and subject_id:
                teacher = get_object_or_404(User, id=teacher_id, role='teacher')
                subject = get_object_or_404(Subject, id=subject_id)
                ClassSubjectTeacher.objects.get_or_create(
                    class_group=class_group,
                    subject=subject,
                    teacher=teacher,
                    academic_year=class_group.academic_year
                )
                messages.success(request, f'Преподаватель {teacher.get_full_name()} назначен на предмет {subject.name}')
        
        elif action == 'remove_subject_teacher':
            subject_teacher_id = request.POST.get('subject_teacher_id')
            if subject_teacher_id:
                ClassSubjectTeacher.objects.filter(id=subject_teacher_id).delete()
                messages.success(request, 'Преподаватель предмета удален')
        
        # После обработки перенаправляем на ту же страницу
        return redirect('administration:class_teachers', class_id=class_group.id)
    
    # GET запрос - показываем страницу
    current_class_teachers = ClassTeacher.objects.filter(
        class_group=class_group,
        academic_year=class_group.academic_year
    ).select_related('teacher')
    
    current_subject_teachers = ClassSubjectTeacher.objects.filter(
        class_group=class_group,
        academic_year=class_group.academic_year
    ).select_related('teacher', 'subject')
    
    current_class_teacher_ids = [ct.teacher.id for ct in current_class_teachers]
    
    context = {
        'class_group': class_group,
        'all_teachers': all_teachers,
        'subjects': subjects,
        'current_class_teachers': current_class_teachers,
        'current_subject_teachers': current_subject_teachers,
        'current_class_teacher_ids': current_class_teacher_ids,
    }
    return render(request, 'administration/class_teachers.html', context)



@login_required
def admin_class_list(request):
    """Управление классами (для администратора)"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    classes = Class.objects.all().order_by('grade', 'letter')
    return render(request, 'administration/class_list.html', {'classes': classes})

@login_required
def create_class(request):
    """Создание нового класса"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        grade = request.POST.get('grade')
        letter = request.POST.get('letter')
        academic_year = request.POST.get('academic_year')
        
        # Проверяем, существует ли уже такой класс
        existing_class = Class.objects.filter(
            grade=grade,
            letter=letter,
            academic_year=academic_year
        ).first()
        
        if existing_class:
            messages.error(request, 'Такой класс уже существует')
        else:
            school = School.objects.first()
            if school:
                class_group = Class.objects.create(
                    school=school,
                    grade=grade,
                    letter=letter,
                    academic_year=academic_year
                )
                messages.success(request, f'Класс {grade}{letter} успешно создан')
            else:
                messages.error(request, 'Сначала создайте школу')
        
        return redirect('administration:admin_class_list')
    
    # Получаем список учебных годов
    current_year = datetime.now().year
    academic_years = [f"{year}-{year+1}" for year in range(current_year-1, current_year+2)]
    
    return render(request, 'administration/create_class.html', {
        'academic_years': academic_years
    })

@login_required
def edit_class(request, class_id):
    """Редактирование класса"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    class_group = get_object_or_404(Class, id=class_id)
    
    if request.method == 'POST':
        class_group.grade = request.POST.get('grade')
        class_group.letter = request.POST.get('letter')
        class_group.academic_year = request.POST.get('academic_year')
        class_group.save()
        messages.success(request, 'Класс успешно обновлен')
        return redirect('administration:admin_class_list')
    
    return render(request, 'administration/edit_class.html', {'class_group': class_group})

@login_required
def class_students(request, class_id):
    """Управление учениками в классе"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    class_group = get_object_or_404(Class, id=class_id)
    
    # Получаем всех учеников
    students = User.objects.filter(role='student').order_by('last_name', 'first_name')
    
    # Получаем текущих учеников класса
    current_students = StudentClass.objects.filter(
        class_group=class_group,
        academic_year=class_group.academic_year
    ).select_related('student')
    
    current_students_ids = [cs.student.id for cs in current_students]
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')
        
        if action == 'add':
            student = get_object_or_404(User, id=student_id, role='student')
            
            # Проверяем, не добавлен ли уже ученик
            existing = StudentClass.objects.filter(
                student=student,
                class_group=class_group,
                academic_year=class_group.academic_year
            ).exists()
            
            if not existing:
                StudentClass.objects.create(
                    student=student,
                    class_group=class_group,
                    academic_year=class_group.academic_year
                )
                messages.success(request, f'Ученик {student.get_full_name()} добавлен в класс')
            else:
                messages.warning(request, f'Ученик {student.get_full_name()} уже в классе')
                
        elif action == 'remove':
            StudentClass.objects.filter(
                student_id=student_id,
                class_group=class_group,
                academic_year=class_group.academic_year
            ).delete()
            messages.success(request, 'Ученик удален из класса')
        
        return redirect('administration:class_students', class_id=class_id)
    
    return render(request, 'administration/class_students.html', {
        'class_group': class_group,
        'students': students,
        'current_students_ids': current_students_ids
    })

@login_required
def subject_list(request):
    """Управление предметами"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    subjects = Subject.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        short_name = request.POST.get('short_name')
        description = request.POST.get('description')
        
        Subject.objects.create(
            name=name,
            short_name=short_name,
            description=description
        )
        messages.success(request, f'Предмет "{name}" успешно добавлен')
        return redirect('administration:subject_list')
    
    return render(request, 'administration/subject_list.html', {'subjects': subjects})

@login_required
def user_list(request):
    """Управление пользователями"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    # Получаем всех пользователей с сортировкой
    users = User.objects.all().order_by('-is_active', 'role', 'last_name', 'first_name')
    
    # Фильтруем по ролям
    students = users.filter(role='student')
    teachers = users.filter(role='teacher')
    admins = users.filter(role='admin')
    
    # Считаем количество
    students_count = students.count()
    teachers_count = teachers.count()
    admins_count = admins.count()
    
    context = {
        'users': users,
        'students': students,
        'teachers': teachers,
        'admins': admins,
        'students_count': students_count,
        'teachers_count': teachers_count,
        'admins_count': admins_count,
    }
    
    return render(request, 'administration/user_list.html', context)

@login_required
def create_user(request):
    """Создание нового пользователя"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        patronymic = request.POST.get('patronymic')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        # Проверяем, существует ли пользователь
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=role
            )
            user.patronymic = patronymic
            user.save()
            messages.success(request, f'Пользователь {username} успешно создан')
            
            # Перенаправление на указанную страницу или список пользователей
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('administration:user_list')
    
    return render(request, 'administration/create_user.html')

@login_required
def edit_user(request, user_id):
    """Редактирование пользователя"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    edit_user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        edit_user.first_name = request.POST.get('first_name')
        edit_user.last_name = request.POST.get('last_name')
        edit_user.patronymic = request.POST.get('patronymic')
        edit_user.email = request.POST.get('email')
        edit_user.phone = request.POST.get('phone')
        edit_user.role = request.POST.get('role')
        edit_user.is_active = request.POST.get('is_active') == 'on'
        
        # Если указан новый пароль
        new_password = request.POST.get('new_password')
        if new_password:
            edit_user.set_password(new_password)
        
        edit_user.save()
        messages.success(request, 'Пользователь успешно обновлен')
        return redirect('administration:user_list')
    
    return render(request, 'administration/edit_user.html', {'edit_user': edit_user})

@login_required
def emergency_settings(request):
    """Настройки режима ЧС"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    school = School.objects.first()
    
    # Получаем статистику для отображения
    from users.models import User
    from administration.models import Class
    from classes.models import Lesson
    from django.utils import timezone
    
    context = {
        'school': school,
        'total_students': User.objects.filter(role='student').count(),
        'total_teachers': User.objects.filter(role='teacher').count(),
        'total_classes': Class.objects.count(),
        'today_lessons': Lesson.objects.filter(date=timezone.now().date()).count(),
    }
    
    return render(request, 'administration/emergency_settings.html', context)

@login_required
def activate_emergency(request):
    """Активация/деактивация режима ЧС"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    if request.method == 'POST':
        school = School.objects.first()
        if school:
            from django.utils import timezone
            
            school.emergency_mode = not school.emergency_mode
            if school.emergency_mode:
                school.emergency_start_date = timezone.now()
                messages.success(request, '⚠️ Режим ЧС АКТИВИРОВАН. Все уроки переведены в дистанционный формат.')
                
                # Здесь можно добавить дополнительную логику:
                # - Отправка уведомлений всем пользователям
                # - Автоматическое создание онлайн-уроков
                # - Блокировка очных занятий
                
            else:
                school.emergency_end_date = timezone.now()
                messages.success(request, '✅ Режим ЧС деактивирован. Школа возвращается к штатной работе.')
            
            school.save()
        else:
            messages.error(request, 'Сначала создайте школу')
    
    return redirect('administration:emergency_settings')
@login_required
def subject_list(request):
    """Управление предметами"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    subjects = Subject.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        short_name = request.POST.get('short_name')
        description = request.POST.get('description')
        
        Subject.objects.create(
            name=name,
            short_name=short_name,
            description=description
        )
        messages.success(request, f'Предмет "{name}" успешно добавлен')
        return redirect('administration:subject_list')
    
    return render(request, 'administration/subject_list.html', {'subjects': subjects})

@login_required
def edit_subject(request, subject_id):
    """Редактирование предмета"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    subject = get_object_or_404(Subject, id=subject_id)
    
    if request.method == 'POST':
        subject.name = request.POST.get('name')
        subject.short_name = request.POST.get('short_name')
        subject.description = request.POST.get('description')
        subject.save()
        
        messages.success(request, f'Предмет "{subject.name}" успешно обновлен')
        return redirect('administration:subject_list')
    
    return render(request, 'administration/subject_list.html', {'subjects': Subject.objects.all()})

@login_required
def delete_subject(request, subject_id):
    """Удаление предмета"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    subject = get_object_or_404(Subject, id=subject_id)
    subject_name = subject.name
    subject.delete()
    
    messages.success(request, f'Предмет "{subject_name}" успешно удален')
    return redirect('administration:subject_list')
@login_required
def delete_user(request, user_id):
    """Удаление пользователя"""
    if not request.user.is_admin():
        messages.error(request, 'У вас нет прав для доступа к этой странице')
        return redirect('users:dashboard')
    
    user = get_object_or_404(User, id=user_id)
    
    # Не даем удалить самого себя
    if user.id == request.user.id:
        messages.error(request, 'Вы не можете удалить самого себя')
        return redirect('administration:user_list')
    
    user_name = user.get_full_name() or user.username
    user.delete()
    
    messages.success(request, f'Пользователь {user_name} успешно удален')
    return redirect('administration:user_list')