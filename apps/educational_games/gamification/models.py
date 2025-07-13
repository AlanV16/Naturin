from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

# ============================================================================
# MODELOS BASE PARA EL SISTEMA DE GAMIFICACIÓN
# ============================================================================

class ActivityType(models.Model):
    """Activity types available"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Activity Type")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Activity Type"
        verbose_name_plural = "Activity Types"

class GameType(models.Model):
    """Game types available"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, verbose_name="Game Type")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Game Type"
        verbose_name_plural = "Game Types"

# ============================================================================
# MODELOS DE AULAS Y ACTIVIDADES
# ============================================================================

class Classroom(models.Model):
    """Virtual classrooms created by teachers"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Classroom Name")
    code = models.CharField(max_length=20, unique=True, verbose_name="Classroom Code")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    grade = models.CharField(max_length=50, blank=True, null=True, verbose_name="Grade")
    section = models.CharField(max_length=10, blank=True, null=True, verbose_name="Section")
    institution_id = models.IntegerField(default=1, verbose_name="Institution ID")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Teacher")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name = "Classroom"
        verbose_name_plural = "Classrooms"

class ClassroomStudent(models.Model):
    """Relationship between students and classrooms"""
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="Classroom")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Student")
    classroom_name = models.CharField(max_length=50, verbose_name="Classroom Name")

    class Meta:
        verbose_name = "Classroom-Student"
        verbose_name_plural = "Classroom-Students"
        unique_together = ('classroom', 'student')

class Activities(models.Model):
    """Activities assigned by teachers to classrooms"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, verbose_name="Title")
    instructions = models.TextField(verbose_name="Instructions")
    activity_type = models.ForeignKey(ActivityType, on_delete=models.CASCADE, verbose_name="Activity Type")
    content_id = models.IntegerField(verbose_name="Content ID")  # Reference to content.Ficha
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="Classroom")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Activity"
        verbose_name_plural = "Activities"

# ============================================================================
# MODELOS DE JUEGOS
# ============================================================================

class Games(models.Model):
    """Educational games available"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Game Name")
    game_type = models.ForeignKey(GameType, on_delete=models.CASCADE, verbose_name="Game Type")
    instructions = models.CharField(max_length=500, verbose_name="Instructions")
    description = models.CharField(max_length=50, verbose_name="Description")
    difficulty_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Difficulty Level"
    )
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Game"
        verbose_name_plural = "Games"

class UserGame(models.Model):
    """User progress in games"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    game = models.ForeignKey(Games, on_delete=models.CASCADE, verbose_name="Game")
    score = models.IntegerField(default=0, verbose_name="Score")
    played_at = models.DateTimeField(auto_now_add=True, verbose_name="Played At")
    
    class Meta:
        verbose_name = "User Game"
        verbose_name_plural = "User Games"
        unique_together = ('user', 'game', 'played_at')

# ============================================================================
# MODELOS DE PROGRESO Y NIVELES
# ============================================================================

class Progress(models.Model):
    """User progress in activities"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User", related_name='gamification_progress')
    activity = models.ForeignKey(Activities, on_delete=models.CASCADE, verbose_name="Activity")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    score = models.IntegerField(default=0, verbose_name="Score")
    completed = models.BooleanField(default=False, verbose_name="Completed")
    
    def __str__(self):
        return f"{self.user} - {self.activity} ({self.score} pts)"
    
    class Meta:
        verbose_name = "Progress"
        verbose_name_plural = "Progress"

class Levels(models.Model):
    """Level system for users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="User")
    level = models.IntegerField(default=1, verbose_name="Level")
    accumulated_points = models.IntegerField(default=0, verbose_name="Accumulated Points")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    def __str__(self):
        return f"{self.user} - Level {self.level} ({self.accumulated_points} pts)"
    
    def calculate_level(self):
        """Calculate level based on accumulated points"""
        if self.accumulated_points < 20:
            return 1
        elif self.accumulated_points < 50:
            return 2
        elif self.accumulated_points < 100:
            return 3
        elif self.accumulated_points < 200:
            return 4
        elif self.accumulated_points < 350:
            return 5
        elif self.accumulated_points < 550:
            return 6
        elif self.accumulated_points < 800:
            return 7
        elif self.accumulated_points < 1100:
            return 8
        elif self.accumulated_points < 1450:
            return 9
        else:
            return 10
    
    def update_level(self):
        """Update level based on points"""
        new_level = self.calculate_level()
        if new_level != self.level:
            self.level = new_level
            self.save()
            return True
        return False
    
    class Meta:
        verbose_name = "Level"
        verbose_name_plural = "Levels"

# ============================================================================
# MODELOS DE INSIGNIAS
# ============================================================================

class Badges(models.Model):
    """Badges that users can earn"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(verbose_name="Description")
    image = models.ImageField(upload_to='badges/', blank=True, null=True, verbose_name="Image")
    condition = models.CharField(max_length=200, verbose_name="Condition")
    required_points = models.IntegerField(default=0, verbose_name="Required Points")
    
    # Badge types
    BADGE_TYPES = [
        ('species_expert', 'Species Expert'),
        ('quiz_master', 'Quiz Master'),
        ('speed_demon', 'Speed Demon'),
        ('explorer', 'Explorer'),
        ('conservationist', 'Conservationist'),
        ('collector', 'Collector'),
        ('first_activity', 'First Activity'),
        ('perfect_score', 'Perfect Score'),
        ('streak_3', '3-Day Streak'),
        ('streak_7', '7-Day Streak'),
        ('streak_30', '30-Day Streak'),
    ]
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES, verbose_name="Badge Type")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Badge"
        verbose_name_plural = "Badges"

class UserBadge(models.Model):
    """Relationship between users and earned badges"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    badge = models.ForeignKey(Badges, on_delete=models.CASCADE, verbose_name="Badge")
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Earned At")
    
    class Meta:
        verbose_name = "User Badge"
        verbose_name_plural = "User Badges"
        unique_together = ('user', 'badge')

# ============================================================================
# MODELOS DE DESAFÍOS Y MISIONES
# ============================================================================

class Challenges(models.Model):
    """Optional challenges for users"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, verbose_name="Name")
    description = models.TextField(verbose_name="Description")
    points = models.IntegerField(default=0, verbose_name="Points")
    minimum_level = models.IntegerField(default=1, verbose_name="Minimum Level")
    
    # Challenge types
    CHALLENGE_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('special', 'Special'),
    ]
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES, verbose_name="Challenge Type")
    
    # Challenge conditions
    condition = models.CharField(max_length=200, verbose_name="Condition")
    start_date = models.DateTimeField(verbose_name="Start Date")
    end_date = models.DateTimeField(verbose_name="End Date")
    active = models.BooleanField(default=True, verbose_name="Active")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Challenge"
        verbose_name_plural = "Challenges"

class UserChallenge(models.Model):
    """User progress in challenges"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    challenge = models.ForeignKey(Challenges, on_delete=models.CASCADE, verbose_name="Challenge")
    completed = models.BooleanField(default=False, verbose_name="Completed")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completed At")
    current_progress = models.IntegerField(default=0, verbose_name="Current Progress")
    
    class Meta:
        verbose_name = "User Challenge"
        verbose_name_plural = "User Challenges"
        unique_together = ('user', 'challenge')

# ============================================================================
# MODELOS DE RANKINGS Y CLASIFICACIONES
# ============================================================================

class Ranking(models.Model):
    """User rankings by classroom"""
    id = models.AutoField(primary_key=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="Classroom")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    total_points = models.IntegerField(default=0, verbose_name="Total Points")
    current_level = models.IntegerField(default=1, verbose_name="Current Level")
    position = models.IntegerField(verbose_name="Position")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    class Meta:
        verbose_name = "Ranking"
        verbose_name_plural = "Rankings"
        unique_together = ('classroom', 'user')
        ordering = ['-total_points', 'current_level']

# ============================================================================
# MODELOS DE RECOMPENSAS
# ============================================================================

class UserReward(models.Model):
    """Rewards earned by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    game = models.ForeignKey(Games, on_delete=models.CASCADE, verbose_name="Game")
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Earned At")
    
    class Meta:
        verbose_name = "User Reward"
        verbose_name_plural = "User Rewards"
        unique_together = ('user', 'game')

# ============================================================================
# MODELOS DE ESTADÍSTICAS Y SEGUIMIENTO
# ============================================================================

class UserStatistics(models.Model):
    """Detailed user statistics"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="User")
    completed_activities = models.IntegerField(default=0, verbose_name="Completed Activities")
    games_played = models.IntegerField(default=0, verbose_name="Games Played")
    badges_earned = models.IntegerField(default=0, verbose_name="Badges Earned")
    challenges_completed = models.IntegerField(default=0, verbose_name="Challenges Completed")
    total_game_time = models.IntegerField(default=0, verbose_name="Total Game Time (minutes)")
    total_score = models.IntegerField(default=0, verbose_name="Total Score")
    current_streak = models.IntegerField(default=0, verbose_name="Current Streak")
    best_streak = models.IntegerField(default=0, verbose_name="Best Streak")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Last Activity")
    
    def __str__(self):
        return f"Statistics for {self.user}"
    
    class Meta:
        verbose_name = "User Statistics"
        verbose_name_plural = "User Statistics"

# ============================================================================
# MODELOS DE CONFIGURACIÓN
# ============================================================================

class GamificationConfiguration(models.Model):
    """Gamification system configuration"""
    id = models.AutoField(primary_key=True)
    configuration_name = models.CharField(max_length=100, verbose_name="Configuration Name")
    value = models.TextField(verbose_name="Value")
    description = models.TextField(blank=True, verbose_name="Description")
    active = models.BooleanField(default=True, verbose_name="Active")
    
    def __str__(self):
        return self.configuration_name

    class Meta:
        verbose_name = "Gamification Configuration"
        verbose_name_plural = "Gamification Configurations"

# ============================================================================
# MODELOS DE LOGS Y AUDITORÍA
# ============================================================================

class GamificationLog(models.Model):
    """Gamification event logs"""
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User")
    event_type = models.CharField(max_length=50, verbose_name="Event Type")
    description = models.TextField(verbose_name="Description")
    points_earned = models.IntegerField(default=0, verbose_name="Points Earned")
    event_date = models.DateTimeField(auto_now_add=True, verbose_name="Event Date")
    
    class Meta:
        verbose_name = "Gamification Log"
        verbose_name_plural = "Gamification Logs"
        ordering = ['-event_date']

# ============================================================================
# MODELOS DE TESTS Y CUESTIONARIOS
# ============================================================================

class Test(models.Model):
    """Tests created by teachers for specific classrooms"""
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200, verbose_name="Test Title")
    description = models.TextField(verbose_name="Description")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, verbose_name="Classroom")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Teacher")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    start_date = models.DateTimeField(verbose_name="Start Date")
    end_date = models.DateTimeField(verbose_name="End Date")
    time_limit = models.IntegerField(default=30, verbose_name="Time Limit (minutes)")
    points_per_question = models.IntegerField(default=10, verbose_name="Points per Question")
    active = models.BooleanField(default=True, verbose_name="Active")
    
    def __str__(self):
        return f"{self.title} - {self.classroom.name}"
    
    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Tests"
        ordering = ['-created_at']

class Question(models.Model):
    """Test questions"""
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Test")
    question = models.TextField(verbose_name="Question")
    question_type = models.CharField(
        max_length=20,
        choices=[
            ('multiple_choice', 'Multiple Choice'),
            ('true_false', 'True/False'),
            ('short_text', 'Short Text'),
        ],
        default='multiple_choice',
        verbose_name="Question Type"
    )
    order = models.IntegerField(default=1, verbose_name="Order")
    points = models.IntegerField(default=10, verbose_name="Points")

    def __str__(self):
        return f"{self.test.title} - Question {self.order}"

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['test', 'order']

class Option(models.Model):
    """Answer options for multiple choice questions"""
    id = models.AutoField(primary_key=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Question")
    text = models.CharField(max_length=500, verbose_name="Option Text")
    is_correct = models.BooleanField(default=False, verbose_name="Is Correct")
    order = models.IntegerField(default=1, verbose_name="Order")

    def __str__(self):
        return f"{self.question.question[:50]} - {self.text[:30]}"

    class Meta:
        verbose_name = "Option"
        verbose_name_plural = "Options"
        ordering = ['question', 'order']

class StudentAnswer(models.Model):
    """Student answers to tests"""
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Test")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Question")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Student")
    text_answer = models.TextField(blank=True, null=True, verbose_name="Text Answer")
    selected_option = models.ForeignKey(
        Option, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True, 
        verbose_name="Selected Option"
    )
    is_correct = models.BooleanField(default=False, verbose_name="Is Correct")
    points_earned = models.IntegerField(default=0, verbose_name="Points Earned")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Answered At")

    def __str__(self):
        return f"{self.student.username} - {self.test.title}"

    class Meta:
        verbose_name = "Student Answer"
        verbose_name_plural = "Student Answers"
        unique_together = ['test', 'question', 'student']

class TestResult(models.Model):
    """Complete student results in tests"""
    id = models.AutoField(primary_key=True)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, verbose_name="Test")
    student = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Student")
    total_score = models.IntegerField(default=0, verbose_name="Total Score")
    max_score = models.IntegerField(default=0, verbose_name="Max Score")
    accuracy_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="Accuracy Percentage"
    )
    correct_questions = models.IntegerField(default=0, verbose_name="Correct Questions")
    total_questions = models.IntegerField(default=0, verbose_name="Total Questions")
    time_used = models.IntegerField(default=0, verbose_name="Time Used (seconds)")
    start_time = models.DateTimeField(verbose_name="Start Time")
    end_time = models.DateTimeField(verbose_name="End Time")
    completed = models.BooleanField(default=False, verbose_name="Completed")

    def __str__(self):
        return f"{self.student.username} - {self.test.title} ({self.accuracy_percentage}%)"

    class Meta:
        verbose_name = "Test Result"
        verbose_name_plural = "Test Results"
        unique_together = ['test', 'student']
        ordering = ['-end_time']

# ============================================================================
# FUNCIONES DE UTILIDAD
# ============================================================================

def generar_codigo_aula():
    """Genera un código único para aulas"""
    return str(uuid.uuid4())[:8].upper()

def calcular_puntos_por_nivel(nivel):
    """Calcula los puntos necesarios para un nivel específico"""
    if nivel == 1:
        return 0
    elif nivel == 2:
        return 20
    elif nivel == 3:
        return 50
    elif nivel == 4:
        return 100
    elif nivel == 5:
        return 200
    elif nivel == 6:
        return 350
    elif nivel == 7:
        return 550
    elif nivel == 8:
        return 800
    elif nivel == 9:
        return 1100
    else:
        return 1450

# ============================================================================
# FUNCIONES DE UTILIDAD PARA TESTS
# ============================================================================

def calcular_puntuacion_test(resultado):
    """Calcula la puntuación total de un test"""
    respuestas = StudentAnswer.objects.filter(
        test=resultado.IDtest,
        student=resultado.IDestudiante
    )
    puntuacion = sum(r.points_earned for r in respuestas)
    return puntuacion

def calcular_porcentaje_acierto(resultado):
    """Calcula el porcentaje de acierto de un test"""
    if resultado.total_preguntas == 0:
        return 0
    return (resultado.preguntas_correctas / resultado.total_preguntas) * 100

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('trivia_completed', 'Trivia Completada'),
        ('activity_completed', 'Actividad Completada'),
        ('quiz_completed', 'Quiz Completado'),
        ('achievement_unlocked', 'Logro Desbloqueado'),
        ('level_up', 'Subida de Nivel'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gamification_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"

# ============================================================================
# MESSAGING SYSTEM MODELS
# ============================================================================

class PrivateMessage(models.Model):
    """Private messages between users"""
    id = models.AutoField(primary_key=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gamification_sent_messages', verbose_name="Sender")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gamification_received_messages', verbose_name="Recipient")
    subject = models.CharField(max_length=200, verbose_name="Subject")
    content = models.TextField(verbose_name="Content")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject}"
    
    class Meta:
        verbose_name = "Private Message"
        verbose_name_plural = "Private Messages"
        ordering = ['-created_at']

class ClassroomMessage(models.Model):
    """Group chat messages for classrooms"""
    id = models.AutoField(primary_key=True)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='gamification_messages', verbose_name="Classroom")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gamification_classroom_messages', verbose_name="Sender")
    content = models.TextField(verbose_name="Content")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    def __str__(self):
        return f"{self.sender.username} in {self.classroom.name}: {self.content[:50]}"
    
    class Meta:
        verbose_name = "Classroom Message"
        verbose_name_plural = "Classroom Messages"
        ordering = ['created_at']

class MessageNotification(models.Model):
    """Notifications for new messages"""
    id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gamification_message_notifications', verbose_name="Recipient")
    message = models.ForeignKey(PrivateMessage, on_delete=models.CASCADE, related_name='gamification_notifications', verbose_name="Message")
    is_read = models.BooleanField(default=False, verbose_name="Is Read")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    
    def __str__(self):
        return f"Message notification for {self.recipient.username}"
    
    class Meta:
        verbose_name = "Message Notification"
        verbose_name_plural = "Message Notifications"
        ordering = ['-created_at']

class PrivateConversation(models.Model):
    """Private conversation between two users"""
    id = models.AutoField(primary_key=True)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gamification_conversations_as_user1', verbose_name="User 1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gamification_conversations_as_user2', verbose_name="User 2")
    last_message = models.ForeignKey(PrivateMessage, on_delete=models.SET_NULL, null=True, blank=True, related_name='gamification_conversation_last_message', verbose_name="Last Message")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    
    def __str__(self):
        return f"Conversation between {self.user1.username} and {self.user2.username}"
    
    class Meta:
        verbose_name = "Private Conversation"
        verbose_name_plural = "Private Conversations"
        unique_together = ['user1', 'user2']
        ordering = ['-updated_at']
    
    def get_other_user(self, current_user):
        """Get the other user in the conversation"""
        if current_user == self.user1:
            return self.user2
        return self.user1
    
    def get_unread_count(self, user):
        """Get unread message count for a user"""
        return PrivateMessage.objects.filter(
            recipient=user,
            conversation=self,
            is_read=False
        ).count()
