from django.db import models
from django.conf import settings
from classes.models import Lesson
from administration.models import Class as SchoolClass

class Attendance(models.Model):
    """Модель посещаемости"""
    ATTENDANCE_STATUS = [
        ('present', 'Присутствовал'),
        ('absent', 'Отсутствовал'),
        ('late', 'Опоздал'),
        ('excused', 'Отсутствовал по уважительной причине'),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='Урок'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='attendances',
        verbose_name='Ученик'
    )
    status = models.CharField(
        max_length=10,
        choices=ATTENDANCE_STATUS,
        default='present',
        verbose_name='Статус'
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='marked_attendances',
        verbose_name='Отметил'
    )
    marked_at = models.DateTimeField(auto_now_add=True, verbose_name='Время отметки')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    class Meta:
        verbose_name = 'Посещаемость'
        verbose_name_plural = 'Посещаемость'
        unique_together = ['lesson', 'student']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.lesson} - {self.get_status_display()}"


class Grade(models.Model):
    """Модель оценки"""
    GRADE_TYPES = [
        ('current', 'Текущая'),
        ('quarter', 'Четвертная'),
        ('final', 'Итоговая'),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='grades',
        verbose_name='Ученик'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='grades',
        null=True,
        blank=True,
        verbose_name='Урок'
    )
    subject = models.CharField(max_length=100, verbose_name='Предмет')
    grade = models.IntegerField(verbose_name='Оценка')
    grade_type = models.CharField(
        max_length=10,
        choices=GRADE_TYPES,
        default='current',
        verbose_name='Тип оценки'
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='given_grades',
        verbose_name='Учитель'
    )
    date = models.DateField(auto_now_add=True, verbose_name='Дата')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    
    class Meta:
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.subject} - {self.grade}"


class Homework(models.Model):
    """Модель домашнего задания"""
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='homeworks',
        verbose_name='Урок'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    due_date = models.DateTimeField(verbose_name='Срок сдачи')
    attachments = models.FileField(
        upload_to='homework/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Вложения'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_homeworks',
        verbose_name='Создал'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Домашнее задание'
        verbose_name_plural = 'Домашние задания'
        ordering = ['-due_date']
    
    def __str__(self):
        return self.title


class HomeworkSubmission(models.Model):
    """Модель сдачи домашнего задания"""
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='submissions',
        verbose_name='Домашнее задание'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='homework_submissions',
        verbose_name='Ученик'
    )
    submission_file = models.FileField(
        upload_to='submissions/%Y/%m/%d/',
        verbose_name='Файл с работой'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name='Время сдачи')
    grade = models.IntegerField(null=True, blank=True, verbose_name='Оценка')
    feedback = models.TextField(blank=True, verbose_name='Отзыв учителя')
    
    class Meta:
        verbose_name = 'Сдача задания'
        verbose_name_plural = 'Сдача заданий'
        unique_together = ['homework', 'student']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.homework.title}"