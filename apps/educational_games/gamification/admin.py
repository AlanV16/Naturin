from django.contrib import admin
from .models import (
    Classroom, ClassroomStudent, ActivityType, GameType, Levels, Games, UserGame, Progress, Badges, UserBadge, Challenges, UserChallenge, Ranking, UserReward, UserStatistics, GamificationConfiguration, GamificationLog, Question, Option, StudentAnswer, TestResult,
)

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'teacher', 'grade', 'section', 'institution_id')
    list_filter = ('grade', 'section', 'institution_id')
    search_fields = ('name', 'code', 'teacher__username')
    readonly_fields = ('code',)

@admin.register(ClassroomStudent)
class ClassroomStudentAdmin(admin.ModelAdmin):
    list_display = ('classroom', 'student', 'classroom_name')
    list_filter = ('classroom',)
    search_fields = ('classroom__name', 'student__username')

@admin.register(ActivityType)
class ActivityTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)

@admin.register(GameType)
class GameTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_filter = ('name',)
    search_fields = ('name',)

@admin.register(Levels)
class LevelsAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'accumulated_points', 'updated_at')
    list_filter = ('level',)
    search_fields = ('user__username',)

@admin.register(Games)
class GamesAdmin(admin.ModelAdmin):
    list_display = ('name', 'game_type', 'instructions', 'description')
    list_filter = ('game_type', 'difficulty_level')
    search_fields = ('name', 'description')

@admin.register(UserGame)
class UserGameAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'score', 'played_at')
    list_filter = ('user', 'game')
    search_fields = ('user__username', 'game__name')

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'score', 'completed', 'date')
    list_filter = ('user', 'activity', 'completed')
    search_fields = ('user__username', 'activity__title')

@admin.register(Badges)
class BadgesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'required_points', 'badge_type')
    list_filter = ('badge_type', 'required_points')
    search_fields = ('name', 'description')

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('user', 'badge', 'earned_at')
    list_filter = ('user', 'badge')
    search_fields = ('user__username', 'badge__name')

@admin.register(Challenges)
class ChallengesAdmin(admin.ModelAdmin):
    list_display = ('name', 'challenge_type', 'points', 'minimum_level', 'active')
    list_filter = ('challenge_type', 'active', 'minimum_level')
    search_fields = ('name', 'description')

@admin.register(UserChallenge)
class UserChallengeAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'completed', 'current_progress', 'completed_at')
    list_filter = ('user', 'challenge', 'completed')
    search_fields = ('user__username', 'challenge__name')

@admin.register(Ranking)
class RankingAdmin(admin.ModelAdmin):
    list_display = ('user', 'classroom', 'total_points', 'current_level', 'position')
    list_filter = ('classroom', 'current_level')
    search_fields = ('user__username', 'classroom__name')

@admin.register(UserReward)
class UserRewardAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'earned_at')
    list_filter = ('user', 'game')
    search_fields = ('user__username', 'game__name')

@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user', 'games_played', 'total_score', 'last_activity')
    list_filter = ('user',)
    search_fields = ('user__username',)

@admin.register(GamificationConfiguration)
class GamificationConfigurationAdmin(admin.ModelAdmin):
    list_display = ('configuration_name', 'value', 'description', 'active')
    list_filter = ('active',)
    search_fields = ('configuration_name', 'description')

@admin.register(GamificationLog)
class GamificationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'event_type', 'description', 'points_earned', 'event_date')
    list_filter = ('event_type', 'event_date')
    search_fields = ('user__username', 'event_type', 'description')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'test', 'question_type', 'order', 'points')
    list_filter = ('question_type', 'order')
    search_fields = ('question', 'test__title')

@admin.register(Option)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')
    list_filter = ('is_correct', 'order')
    search_fields = ('text', 'question__question')

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ('student', 'question', 'selected_option', 'is_correct', 'points_earned')
    list_filter = ('student', 'question', 'is_correct')
    search_fields = ('student__username', 'question__question')

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'test', 'total_score', 'max_score', 'accuracy_percentage', 'completed')
    list_filter = ('test', 'completed')
    search_fields = ('student__username', 'test__title') 