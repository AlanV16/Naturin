from apps.users.models import User
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Badge(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')
    points_required = models.IntegerField(default=0)

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
