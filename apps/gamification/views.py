from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Game

@login_required
def game_detail(request, pk):
    game = get_object_or_404(Game, pk=pk)
    return render(request, 'gamification/game_detail.html', {
        'game': game
    })

@login_required
def complete_game(request, pk):
    game = get_object_or_404(Game, pk=pk)
    # Lógica para otorgar puntos y registrar juego completado
    return JsonResponse({'success': True, 'points': game.points_per_play})