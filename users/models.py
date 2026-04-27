from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Расширенная модель пользователя"""
    
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Администратор'
        TEACHER = 'teacher', 'Учитель'
        STUDENT = 'student', 'Ученик'
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name='Роль'
    )
    patronymic = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Отчество'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True,
        verbose_name='Аватар'
    )
    is_active_remote = models.BooleanField(
        default=True,
        verbose_name='Активен в дистанционном режиме'
    )
    last_online = models.DateTimeField(
        auto_now=True,
        verbose_name='Последний онлайн'
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()
    
    def get_full_name(self):
        """Полное имя с отчеством"""
        parts = [self.last_name, self.first_name, self.patronymic]
        return ' '.join(filter(None, parts))
    
    def get_short_name(self):
        """Краткое имя"""
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name[0]}."
        return self.username
    
    def is_teacher(self):
        return self.role == self.Role.TEACHER or self.is_superuser
    
    def is_student(self):
        return self.role == self.Role.STUDENT
    
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser