from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
    path('', views.home, name='home'),
    path('quiz/start/', views.start, name='start'),
    path('quiz/<int:pk>/question/<int:position>/', views.question, name='question'),
    path('quiz/<int:pk>/answer/<int:position>/', views.save, name='save'),
    path('quiz/<int:pk>/confirm/', views.confirm, name='confirm'),
    path('quiz/<int:pk>/submit/', views.submit, name='submit'),
    path('quiz/<int:pk>/result/', views.result, name='result'),
    path('quiz/<int:pk>/override/', views.override, name='override'),
]
