from django.db import models
from django.conf import settings
from django.utils import timezone
from administration.models import Class as SchoolClass

class ClassChat(models.Model):
    """Чат для конкретного класса"""
    class_group = models.OneToOneField(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='chat',
        verbose_name='Класс'
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='class_chats',
        verbose_name='Участники'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Чат класса'
        verbose_name_plural = 'Чаты классов'
    
    def __str__(self):
        return f"Чат {self.class_group}"

class ClassMessage(models.Model):
    """Сообщение в чате класса"""
    chat = models.ForeignKey(
        ClassChat,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Чат'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_class_messages',
        verbose_name='Отправитель'
    )
    text = models.TextField(verbose_name='Текст сообщения', blank=True)
    file = models.FileField(
        upload_to='chat_files/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Вложение'
    )
    image = models.ImageField(
        upload_to='chat_images/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Дата отправки')
    
    class Meta:
        verbose_name = 'Сообщение чата'
        verbose_name_plural = 'Сообщения чатов'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.get_full_name()}: {self.text[:50] if self.text else '[Файл]'}"
    
    def has_attachment(self):
        return bool(self.file or self.image)