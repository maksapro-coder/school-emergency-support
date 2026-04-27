#!/bin/sh

# Применение миграций
python manage.py migrate --noinput

# Сбор статики
python manage.py collectstatic --noinput

# Создание суперпользователя (если не существует)
python manage.py shell -c "
from users.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created')
"

# Запуск сервера
exec "$@"