from apps.users.models import User
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Badge(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')
    points_required = models.IntegerField(default=0)
    users = models.ManyToManyField(User, related_name='earned_badges', blank=True)

    def __str__(self):
        return self.name

class Challenge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    points = models.IntegerField()
    badge = models.ForeignKey(Badge, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    grade = models.CharField(max_length=20, choices=[('Primer Grado', 'Primer Grado'), ('Segundo Grado', 'Segundo Grado')], default='Primer Grado')
    capability = models.CharField(max_length=50, choices=[('Pensamiento Crítico', 'Pensamiento Crítico'), ('Resolución de Problemas', 'Resolución de Problemas')], default='Pensamiento Crítico')
    steps = models.JSONField(default=list, blank=True)
    completed_by = models.ManyToManyField(User, related_name='completed_challenges', blank=True)

    def __str__(self):
        return self.name

class UserChallenge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'challenge')

    def __str__(self):
        return f"{self.user} - {self.challenge}"

class Game(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    url = models.CharField(max_length=200)
    points_per_play = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Reward(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    required_points = models.IntegerField()
    image = models.ImageField(upload_to='rewards/')
    users = models.ManyToManyField(User, related_name='earned_rewards', blank=True)
    capability = models.CharField(max_length=50, choices=[('Pensamiento Crítico', 'Pensamiento Crítico'), ('Resolución de Problemas', 'Resolución de Problemas')], default='Pensamiento Crítico')

    def __str__(self):
        return self.name

class Level(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_level = models.IntegerField(default=1)
    accumulated_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user} - Level {self.current_level}"

class GamifiedActivity(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    points = models.IntegerField()
    grade = models.CharField(max_length=20, choices=[('Primer Grado', 'Primer Grado'), ('Segundo Grado', 'Segundo Grado')])
    capability = models.CharField(max_length=50, choices=[('Pensamiento Crítico', 'Pensamiento Crítico'), ('Resolución de Problemas', 'Resolución de Problemas')])
    completed_by = models.ManyToManyField(User, related_name='completed_activities', blank=True)

    def __str__(self):
        return self.name

class Ranking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    points = models.IntegerField()

    def __str__(self):
        return f"{self.user} - {self.points}"

class Mission(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=[('Diaria', 'Diaria'), ('Semanal', 'Semanal'), ('Especial', 'Especial')])
    objectives = models.JSONField(default=list, blank=True)
    points = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    capability = models.CharField(max_length=50, choices=[('Pensamiento Crítico', 'Pensamiento Crítico'), ('Resolución de Problemas', 'Resolución de Problemas')])

    def __str__(self):
        return self.name

class TriviaQuestion(models.Model):
    grade = models.CharField(max_length=20, choices=[('Primer Grado', 'Primer Grado'), ('Segundo Grado', 'Segundo Grado')])
    capability = models.CharField(max_length=50, choices=[('Pensamiento Crítico', 'Pensamiento Crítico'), ('Resolución de Problemas', 'Resolución de Problemas')])
    question = models.CharField(max_length=200)
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.IntegerField()
    image = models.ImageField(upload_to='trivia_images/', null=True, blank=True)
    explanation = models.TextField()

    def __str__(self):
        return self.question[:50]

class Certificate(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    date = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='certificates/', null=True, blank=True)
    capability = models.CharField(max_length=50, choices=[('Pensamiento Crítico', 'Pensamiento Crítico'), ('Resolución de Problemas', 'Resolución de Problemas')])

    def __str__(self):
        return f"{self.name} - {self.user}"