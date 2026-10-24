from django.conf import settings


def desktop_mode(request):
    return {'desktop_mode': settings.DESKTOP_MODE}
