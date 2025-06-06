from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from .models import Classroom, Assignment

@login_required
def classroom_detail(request, code):
    classroom = get_object_or_404(Classroom, code=code)
    assignments = classroom.assignments.all().order_by('-due_date')
    
    if request.user.user_type == 2:  # Docente
        submissions = Submission.objects.filter(assignment__classroom=classroom)
    else:  # Estudiante
        submissions = Submission.objects.filter(
            assignment__classroom=classroom,
            student=request.user
        )
    
    return render(request, 'classrooms/classroom_detail.html', {
        'classroom': classroom,
        'assignments': assignments,
        'submissions': submissions
    })