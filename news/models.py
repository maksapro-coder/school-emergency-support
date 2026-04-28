from django.db import models
from django.conf import settings
from django.utils import timezone

class NewsCategory(models.Model):
    """Категория новостей"""
    name = models.CharField(max_length=50, verbose_name='Название')
    icon = models.CharField(max_length=50, default='fas fa-newspaper', verbose_name='Иконка')
    color = models.CharField(max_length=20, default='primary', verbose_name='Цвет')
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name

class News(models.Model):
    """Модель новости"""
    PRIORITY_CHOICES = [
        ('emergency', '🚨 ЧС'),  # Исправлено - закрыта кавычка
        ('high', '⭐ Высокий приоритет'),
        ('normal', '📄 Обычный'),
        ('low', '📌 Низкий'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    content = models.TextField(verbose_name='Содержание')
    category = models.ForeignKey(
        NewsCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news',
        verbose_name='Категория'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name='Приоритет'
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор'
    )
    image = models.ImageField(
        upload_to='news/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    is_emergency = models.BooleanField(default=False, verbose_name='Связано с ЧС')
    published_at = models.DateTimeField(default=timezone.now, verbose_name='Дата публикации')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-is_emergency', '-priority', '-published_at']
    
    def __str__(self):
        return self.title

class NewsComment(models.Model):
    """Комментарии к новостям"""
    news = models.ForeignKey(News, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()}: {self.comment[:50]}"