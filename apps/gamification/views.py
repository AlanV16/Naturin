from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from .models import Badge, Reward, Level, GamifiedActivity, Challenge, Mission, TriviaQuestion, Certificate
import json
from django.core.files.base import ContentFile
from django.conf import settings

class BadgeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        points = Level.objects.get(user=user).accumulated_points
        badge = Badge.objects.filter(points_required__lte=points).order_by('-points_required').first()
        if badge and user not in badge.users.all():
            badge.users.add(user)
            return Response({'status': 'badge_earned', 'name': badge.name, 'description': badge.description})
        return Response({'status': 'no_new_badge'})

class RewardView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        grade = request.user.profile.grade
        rewards = Reward.objects.filter(required_points__lte=Level.objects.get(user=request.user).accumulated_points)
        return Response([{
            'name': r.name,
            'description': r.description,
            'capability': r.capability
        } for r in rewards if r.users.filter(id=request.user.id).exists()])

class GamifiedActivityView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        activity = GamifiedActivity.objects.get(id=request.data['activity_id'])
        if activity.grade == request.user.profile.grade:
            activity.completed_by.add(request.user)
            level = Level.objects.get(user=request.user)
            level.accumulated_points += activity.points
            level.save()
            return Response({'status': 'completed', 'capability': activity.capability})
        return Response({'error': 'Grade does not match'}, status=400)

class ChallengeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        challenge = Challenge.objects.get(id=request.data['challenge_id'])
        if challenge.grade == request.user.profile.grade:
            challenge.completed_by.add(request.user)
            level = Level.objects.get(user=request.user)
            level.accumulated_points += challenge.points
            level.save()
            return Response({'status': 'completed', 'capability': challenge.capability})
        return Response({'error': 'Grade does not match'}, status=400)

class TriviaView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        question = TriviaQuestion.objects.filter(grade=request.user.profile.grade).order_by('?').first()
        return Response({
            'id': question.id,
            'question': question.question,
            'options': question.options,
            'capability': question.capability,
            'explanation': question.explanation
        })
    
    def post(self, request):
        question = TriviaQuestion.objects.get(id=request.data['question_id'])
        correct = request.data['answer'] == question.correct_answer
        if correct:
            level = Level.objects.get(user=request.user)
            level.accumulated_points += 10
            level.save()
        return Response({
            'correct': correct,
            'points': 10 if correct else 0,
            'explanation': question.explanation,
            'capability': question.capability
        })

class CertificateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        level = Level.objects.get(user=user)
        certificate = Certificate.objects.create(
            user=user,
            name=f"Certificado de {level.current_level} Nivel",
            capability=request.data.get('capability', 'Pensamiento Crítico')
        )
        response = HttpResponse(content_type='application/pdf')
        p = canvas.Canvas(response)
        p.drawString(100, 750, f"Certificado de Logro")
        p.drawString(100, 700, f"Nombre: {user.get_full_name()}")
        p.drawString(100, 650, f"Nivel: {level.current_level}")
        p.drawString(100, 600, f"Puntos Acumulados: {level.accumulated_points}")
        p.drawString(100, 550, f"Fecha: {certificate.date.strftime('%d/%m/%Y')}")
        p.setFont("Helvetica", 20)
        p.setFillAlpha(0.3)
        p.drawString(200, 400, "NatureIn")
        p.setFillAlpha(1.0)
        p.showPage()
        p.save()
        certificate.file.save(f"{user.id}_{certificate.name}.pdf", ContentFile(response.content))
        return response