from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from .models import ClassChat, ClassMessage
from .forms import ClassMessageForm
from administration.models import Class as SchoolClass, StudentClass, ClassTeacher

@login_required
def class_chat_list(request):
    """Список чатов классов пользователя"""
    from administration.models import StudentClass
    from django.db.models import Q
    
    # Получаем классы пользователя
    if request.user.is_teacher():
        user_classes = SchoolClass.objects.filter(
            Q(class_teachers__teacher=request.user) |
            Q(lessons__teacher=request.user)
        ).distinct()
    else:
        student_classes = StudentClass.objects.filter(student=request.user)
        user_classes = [sc.class_group for sc in student_classes]
    
    class_chats = []
    for class_group in user_classes:
        chat, created = ClassChat.objects.get_or_create(class_group=class_group)
        
        if request.user not in chat.participants.all():
            chat.participants.add(request.user)
        
        last_message = chat.messages.order_by('-created_at').first()
        
        # Форматируем последнее сообщение для отображения
        last_message_text = ""
        if last_message:
            if last_message.text:
                last_message_text = last_message.text[:50]
            elif last_message.file:
                last_message_text = f"📎 {last_message.file.name.split('/')[-1][:30]}"
            elif last_message.image:
                last_message_text = f"🖼️ Изображение"
            else:
                last_message_text = "Новое сообщение"
            
            # Добавляем имя отправителя
            last_message_text = f"{last_message.sender.get_short_name()}: {last_message_text}"
        else:
            last_message_text = "Нет сообщений"
        
        unread_count = chat.messages.filter(
            Q(is_read=False) & ~Q(sender=request.user)
        ).count()
        
        class_chats.append({
            'chat': chat,
            'class_group': class_group,
            'last_message': last_message,
            'last_message_text': last_message_text,
            'unread_count': unread_count,
        })
    
    return render(request, 'chat/class_chat_list.html', {'class_chats': class_chats})


@login_required
def class_chat_detail(request, class_id):
    """Детальная страница чата класса"""
    from administration.models import StudentClass
    
    class_group = get_object_or_404(SchoolClass, id=class_id)
    
    if not request.user.is_teacher():
        if not StudentClass.objects.filter(student=request.user, class_group=class_group).exists():
            messages.error(request, 'У вас нет доступа к этому чату')
            return redirect('chat:class_list')
    
    chat, created = ClassChat.objects.get_or_create(class_group=class_group)
    
    if request.user not in chat.participants.all():
        chat.participants.add(request.user)
    
    ClassMessage.objects.filter(
        chat=chat,
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)
    
    # Обработка POST запроса
    if request.method == 'POST':
        form = ClassMessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.chat = chat
            message.sender = request.user
            message.save()
            
            chat.updated_at = timezone.now()
            chat.save()
            
            # Возвращаем JSON для AJAX запросов
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message_id': message.id})
            
            return redirect('chat:class_detail', class_id=class_group.id)
    
    # GET запрос - показываем страницу
    form = ClassMessageForm()
    messages_list = chat.messages.all().order_by('created_at').select_related('sender')
    participants = chat.participants.all().order_by('role', 'last_name')
    
    context = {
        'chat': chat,
        'class_group': class_group,
        'messages': messages_list,
        'form': form,
        'participants': participants,
    }
    return render(request, 'chat/class_chat_detail.html', context)

@login_required
def get_new_messages(request, class_id):
    """API для получения новых сообщений"""
    class_group = get_object_or_404(SchoolClass, id=class_id)
    chat = ClassChat.objects.get(class_group=class_group)
    last_message_id = request.GET.get('last_id', 0)
    
    # Если last_id=0, возвращаем ВСЕ сообщения (историю)
    if last_message_id == '0':
        new_messages = chat.messages.all().order_by('created_at').select_related('sender')
    else:
        new_messages = chat.messages.filter(
            id__gt=last_message_id
        ).order_by('created_at').select_related('sender')
    
    messages_data = []
    for msg in new_messages:
        data = {
            'id': msg.id,
            'text': msg.text,
            'sender_name': msg.sender.get_full_name(),
            'sender_id': msg.sender.id,
            'time': msg.created_at.strftime('%H:%M'),
            'is_own': msg.sender.id == request.user.id,
        }
        
        if msg.image:
            data['image_url'] = msg.image.url
        
        if msg.file:
            data['file_url'] = msg.file.url
            filename = msg.file.name.split('/')[-1]
            if len(filename) > 30:
                filename = filename[:27] + '...'
            data['file_name'] = filename
        
        messages_data.append(data)
    
    # Отмечаем новые сообщения как прочитанные (только для новых)
    if last_message_id != '0':
        chat.messages.filter(
            id__gt=last_message_id
        ).exclude(sender=request.user).update(is_read=True)
    
    return JsonResponse({'messages': messages_data})

def get_file(request, message_id):
    """Получение файла из сообщения"""
    message = get_object_or_404(ClassMessage, id=message_id)
    
    # Проверяем доступ к чату
    if request.user not in message.chat.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if message.file:
        return redirect(message.file.url)
    elif message.image:
        return redirect(message.image.url)
    else:
        return JsonResponse({'error': 'No file'}, status=404)