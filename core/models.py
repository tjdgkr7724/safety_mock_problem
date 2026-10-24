from django.db import models


class Question(models.Model):
    number = models.PositiveIntegerField(unique=True)
    category = models.CharField(max_length=10, choices=[('easy', '하'), ('medium', '중'), ('hard', '상'), ('short', '단답형')])
    text = models.TextField()
    choices = models.JSONField(default=list, blank=True)
    correct_choice = models.PositiveSmallIntegerField(null=True, blank=True)
    answer = models.TextField()
    explanation = models.TextField()
    source = models.CharField(max_length=200)
    accepted_answers = models.JSONField(default=list, blank=True)
    keyword_groups = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f'{self.number}. {self.text[:60]}'


class Attempt(models.Model):
    owner = models.CharField(max_length=32, db_index=True)
    questions = models.JSONField()
    answers = models.JSONField(default=dict)
    submitted = models.BooleanField(default=False)
    short_override = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
