from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import News, NewsCategory
from .forms import NewsForm, CommentForm
from administration.models import School

def news_list(request):
    """Список новостей"""
    # Получаем параметры фильтрации
    category_id = request.GET.get('category')
    search = request.GET.get('search')
    is_emergency = request.GET.get('emergency')
    
    # Базовый запрос
    news = News.objects.filter(is_published=True)
    
    # Фильтрация
    if category_id:
        news = news.filter(category_id=category_id)
    if search:
        news = news.filter(Q(title__icontains=search) | Q(content__icontains=search))
    if is_emergency:
        news = news.filter(is_emergency=True)
    
    # Пагинация
    paginator = Paginator(news, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получаем школу для проверки режима ЧС
    school = School.objects.first()
    
    context = {
        'news': page_obj,
        'categories': NewsCategory.objects.all(),
        'selected_category': category_id,
        'search_query': search,
        'school': school,
        'is_emergency_mode': school.emergency_mode if school else False,
    }
    return render(request, 'news/news_list.html', context)

@login_required
def news_detail(request, news_id):
    """Детальная страница новости"""
    news = get_object_or_404(News, id=news_id, is_published=True)
    comments = news.comments.all()
    school = School.objects.first()
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Войдите чтобы оставить комментарий')
            return redirect('users:login')
        
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.news = news
            comment.user = request.user
            comment.save()
            messages.success(request, 'Комментарий добавлен')
            return redirect('news:detail', news_id=news.id)
    else:
        form = CommentForm()
    
    context = {
        'news': news,
        'comments': comments,
        'form': form,
        'school': school,
    }
    return render(request, 'news/news_detail.html', context)

@login_required
def news_create(request):
    """Создание новости (только для админа и учителя)"""
    if not request.user.is_admin() and not request.user.is_teacher():
        messages.error(request, 'У вас нет прав для создания новостей')
        return redirect('news:list')
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            messages.success(request, 'Новость успешно создана')
            return redirect('news:detail', news_id=news.id)
    else:
        form = NewsForm()
    
    return render(request, 'news/news_form.html', {'form': form, 'title': 'Создать новость'})

@login_required
def news_edit(request, news_id):
    """Редактирование новости (только для автора, админа и учителя)"""
    news = get_object_or_404(News, id=news_id)
    
    if not request.user.is_admin() and news.author != request.user and not request.user.is_teacher():
        messages.error(request, 'У вас нет прав для редактирования')
        return redirect('news:detail', news_id=news.id)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            messages.success(request, 'Новость обновлена')
            return redirect('news:detail', news_id=news.id)
    else:
        form = NewsForm(instance=news)
    
    return render(request, 'news/news_form.html', {'form': form, 'title': 'Редактировать новость', 'news': news})