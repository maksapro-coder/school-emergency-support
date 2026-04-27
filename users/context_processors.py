from administration.models import School

def school_info(request):
    """Добавляет информацию о школе во все шаблоны"""
    if request.user.is_authenticated:
        school = School.objects.first()
        return {'school': school}
    return {}