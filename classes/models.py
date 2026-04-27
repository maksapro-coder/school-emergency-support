from django.db import models
from django.conf import settings
from administration.models import Class as SchoolClass, Subject

class Lesson(models.Model):
    """Модель урока"""
    
    class_group = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Класс'
        
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Предмет'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='lessons_taught',
        verbose_name='Учитель'
    )
    topic = models.CharField(max_length=200, verbose_name='Тема урока')
    description = models.TextField(blank=True, verbose_name='Описание')
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    recording_url = models.URLField(blank=True, null=True, verbose_name='Ссылка на запись урока')
    recording_file = models.FileField(upload_to='recordings/%Y/%m/%d/', blank=True, null=True, verbose_name='Файл записи')
    # Материалы к уроку
    materials = models.FileField(
        upload_to='lesson_materials/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Материалы'
    )
    video_link = models.URLField(blank=True, verbose_name='Ссылка на видео')
    
    # WebRTC комната
    room_name = models.CharField(max_length=100, unique=True, verbose_name='Название комнаты')
    is_active = models.BooleanField(default=False, verbose_name='Активен')
    recording_url = models.URLField(blank=True, verbose_name='Запись урока')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.subject.name} - {self.class_group} ({self.date})"
    
    def get_duration(self):
        """Длительность урока в минутах"""
        from datetime import datetime
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        duration = end - start
        return duration.seconds // 60

class Schedule(models.Model):
    """Модель расписания"""
    class_group = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Класс'
    )
    
    DAYS_OF_WEEK = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    ]
    
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name='День недели')
    lesson_number = models.IntegerField(verbose_name='Номер урока')
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name='Предмет'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        verbose_name='Учитель'
    )
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    academic_year = models.CharField(max_length=9, verbose_name='Учебный год')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписания'
        ordering = ['day_of_week', 'lesson_number']
        unique_together = ['class_group', 'day_of_week', 'lesson_number', 'academic_year']
    
    def __str__(self):
        return f"{self.class_group} - {self.get_day_of_week_display()} - {self.lesson_number} урок"
class Lesson(models.Model):
    """Модель урока"""
    class_group = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Класс'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Предмет'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        related_name='lessons_taught',
        verbose_name='Учитель'
    )
    topic = models.CharField(max_length=200, verbose_name='Тема урока')
    description = models.TextField(blank=True, verbose_name='Описание')
    date = models.DateField(verbose_name='Дата')
    start_time = models.TimeField(verbose_name='Время начала')
    end_time = models.TimeField(verbose_name='Время окончания')
    
    # Материалы к уроку
    materials = models.FileField(
        upload_to='lesson_materials/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Материалы'
    )
    video_link = models.URLField(blank=True, verbose_name='Ссылка на видео')
    
    # WebRTC комната
    room_name = models.CharField(max_length=100, unique=True, verbose_name='Название комнаты')
    is_active = models.BooleanField(default=False, verbose_name='Активен')
    recording_url = models.URLField(blank=True, verbose_name='Запись урока')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.subject.name} - {self.class_group} ({self.date})"
    
    def get_duration(self):
        """Длительность урока в минутах"""
        from datetime import datetime
        start = datetime.combine(self.date, self.start_time)
        end = datetime.combine(self.date, self.end_time)
        duration = end - start
        return duration.seconds // 60
    
    def save(self, *args, **kwargs):
        if not self.room_name:
            # Генерируем уникальное имя комнаты
            import uuid
            self.room_name = f"lesson_{self.class_group.id}_{self.date}_{uuid.uuid4().hex[:8]}"
        super().save(*args, **kwargs)