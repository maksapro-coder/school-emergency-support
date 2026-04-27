import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from classes.models import Lesson
from control.models import Attendance
from datetime import datetime

class LessonConsumer(AsyncWebsocketConsumer):
    # Хранилище пользователей в комнатах
    room_users = {}
    
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'lesson_{self.room_name}'
        
        user = self.scope['user']
        print(f"🔌 WebSocket connect: {user.get_full_name()} (ID: {user.id}) to room {self.room_name}")
        
        # Инициализируем комнату
        if self.room_name not in self.room_users:
            self.room_users[self.room_name] = {}
        
        # Добавляем пользователя в комнату
        self.room_users[self.room_name][user.id] = user.get_full_name()
        print(f"👥 Текущие пользователи в комнате: {self.room_users[self.room_name]}")
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        print(f"✅ WebSocket принят для {user.get_full_name()}")
        
        # Отправляем новому пользователю список всех текущих пользователей
        current_users = self.room_users[self.room_name]
        print(f"📋 Отправляем список пользователей {user.get_full_name()}: {current_users}")
        
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': [{'id': uid, 'name': name} for uid, name in current_users.items()]
        }))
        
        # Сообщаем всем ОСТАЛЬНЫМ о новом пользователе
        print(f"📢 Рассылаем user_joined всем в группе {self.room_group_name}")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': user.id,
                'username': user.get_full_name(),
            }
        )
    
    async def disconnect(self, close_code):
        user = self.scope['user']
        print(f"🔌 WebSocket disconnect: {user.get_full_name()} (ID: {user.id})")
        
        # Удаляем пользователя из комнаты
        if self.room_name in self.room_users and user.id in self.room_users[self.room_name]:
            del self.room_users[self.room_name][user.id]
            print(f"👥 Пользователь удален. Остались: {self.room_users[self.room_name]}")
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Сообщаем всем о выходе пользователя
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user_id': user.id,
                'username': user.get_full_name(),
            }
        )
    
    async def receive(self, text_data):
        user = self.scope['user']
        data = json.loads(text_data)
        message_type = data.get('type')
        
        print(f"📥 Получено {message_type} от {user.get_full_name()}")
        
        if message_type == 'offer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'relay_offer',
                    'offer': data['offer'],
                    'user_id': user.id,
                    'username': user.get_full_name()
                }
            )
        
        elif message_type == 'answer':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'relay_answer',
                    'answer': data['answer'],
                    'target_user_id': data['target_user_id'],
                    'user_id': user.id
                }
            )
        
        elif message_type == 'ice-candidate':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'relay_ice_candidate',
                    'candidate': data['candidate'],
                    'target_user_id': data['target_user_id'],
                    'user_id': user.id
                }
            )
        
        elif message_type == 'chat-message':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': data['message'],
                    'user_id': user.id,
                    'username': user.get_full_name(),
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        elif message_type == 'raise-hand':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'raise_hand',
                    'user_id': user.id,
                    'username': user.get_full_name(),
                }
            )
        
        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': user.id,
                    'username': user.get_full_name(),
                    'is_typing': data['is_typing']
                }
            )
        elif message_type == 'screen_share_started':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'screen_share_started',
                    'user_id': user.id,
                    'username': user.get_full_name()
                }
            )

        elif message_type == 'screen_share_stopped':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'screen_share_stopped',
                    'user_id': user.id,
                    'username': user.get_full_name()
                }
            )
    
    async def user_joined(self, event):
        print(f"📢 Отправляем user_joined клиенту: {event['username']}")
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def user_left(self, event):
        print(f"📢 Отправляем user_left клиенту: {event['username']}")
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def user_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_list',
            'users': event['users']
        }))
    
    async def relay_offer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'offer',
            'offer': event['offer'],
            'user_id': event['user_id'],
            'username': event['username']
        }))
    
    async def relay_answer(self, event):
        if self.scope['user'].id == event['target_user_id']:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer'],
                'user_id': event['user_id']
            }))
    
    async def relay_ice_candidate(self, event):
        if self.scope['user'].id == event['target_user_id']:
            await self.send(text_data=json.dumps({
                'type': 'ice-candidate',
                'candidate': event['candidate'],
                'user_id': event['user_id']
            }))
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat-message',
            'message': event['message'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event['timestamp']
        }))
    
    async def raise_hand(self, event):
        await self.send(text_data=json.dumps({
            'type': 'raise-hand',
            'user_id': event['user_id'],
            'username': event['username'],
        }))
    
    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    async def start_recording(self, event):
        """Начало записи"""
        await self.send(text_data=json.dumps({
            'type': 'recording_started',
            'recording_url': event.get('recording_url', '')
        }))

    async def stop_recording(self, event):
        """Остановка записи"""
        await self.send(text_data=json.dumps({
            'type': 'recording_stopped'
        }))

    async def screen_share_started(self, event):
        """Начало демонстрации экрана"""
        await self.send(text_data=json.dumps({
            'type': 'screen_share_started',
            'user_id': event['user_id'],
            'username': event['username']
        }))

    async def screen_share_stopped(self, event):
        """Остановка демонстрации экрана"""
        await self.send(text_data=json.dumps({
            'type': 'screen_share_stopped',
            'user_id': event['user_id'],
            'username': event['username']
        }))