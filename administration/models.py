from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class School(models.Model):
    """Модель школы"""
    name = models.CharField(max_length=200, verbose_name='Название школы')
    address = models.TextField(verbose_name='Адрес')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    director_name = models.CharField(max_length=100, verbose_name='Директор')
    emergency_mode = models.BooleanField(
        default=False,
        verbose_name='Режим ЧС активен'
    )
    emergency_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата начала ЧС'
    )
    emergency_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата окончания ЧС'
    )
    
    class Meta:
        verbose_name = 'Школа'
        verbose_name_plural = 'Школы'
    
    def __str__(self):
        return self.name

class Class(models.Model):
    """Модель класса"""
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classes',
        verbose_name='Школа'
    )
    grade = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(11)],
        verbose_name='Класс'
    )
    letter = models.CharField(max_length=2, verbose_name='Буква класса')
    academic_year = models.CharField(max_length=9, verbose_name='Учебный год')
    
    class Meta:
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'
        unique_together = ['school', 'grade', 'letter', 'academic_year']
    
    def __str__(self):
        return f"{self.grade}{self.letter} ({self.academic_year})"

class ClassTeacher(models.Model):
    """Классный руководитель"""
    class_group = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='class_teachers',
        verbose_name='Класс'
    )
    teacher = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'teacher'},
        verbose_name='Учитель'
    )
    academic_year = models.CharField(max_length=9, verbose_name='Учебный год')
    
    class Meta:
        verbose_name = 'Классный руководитель'
        verbose_name_plural = 'Классные руководители'
        unique_together = ['class_group', 'teacher', 'academic_year']
    
    def __str__(self):
        return f"{self.class_group} - {self.teacher.get_full_name()}"

class StudentClass(models.Model):
    """Ученик в классе"""
    student = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'student'},
        related_name='student_classes',
        verbose_name='Ученик'
    )
    class_group = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='students',
        verbose_name='Класс'
    )
    academic_year = models.CharField(max_length=9, verbose_name='Учебный год')
    enrollment_date = models.DateField(auto_now_add=True, verbose_name='Дата зачисления')
    
    class Meta:
        verbose_name = 'Ученик в классе'
        verbose_name_plural = 'Ученики в классах'
        unique_together = ['student', 'class_group', 'academic_year']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.class_group}"
class Subject(models.Model):
    """Модель учебного предмета"""
    name = models.CharField(max_length=100, verbose_name='Название предмета')
    short_name = models.CharField(max_length=20, verbose_name='Краткое название')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Предмет'
        verbose_name_plural = 'Предметы'
    
    def __str__(self):
        return self.name