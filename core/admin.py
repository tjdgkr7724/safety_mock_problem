from django.contrib import admin
from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('number', 'category', 'text')
    list_filter = ('category',)
    search_fields = ('text', 'answer')
    ordering = ('number',)
