import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Инициализируем Django ASGI application заранее
django_asgi_app = get_asgi_application()

# Теперь можно импортировать остальное
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path, re_path
from classes.consumers import LessonConsumer

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter([
            path('ws/lesson/<str:room_name>/', LessonConsumer.as_asgi()),
        ])
    ),
})