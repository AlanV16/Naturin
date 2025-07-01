from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Guide
from .forms import GuideForm


def guide_list(request):
    guides = Guide.objects.filter(is_public=True)
    return render(request, 'pedagogical_guides/guide_list.html', {'guides': guides})


@login_required
def guide_upload(request):
    if request.method == 'POST':
        form = GuideForm(request.POST, request.FILES)
        if form.is_valid():
            guide = form.save(commit=False)
            guide.author = request.user
            guide.save()
            return redirect('pedagogical_guides:guide_list')
    else:
        form = GuideForm()
    return render(request, 'pedagogical_guides/guide_form.html', {'form': form})


def guide_download(request, pk):
    guide = get_object_or_404(Guide, pk=pk, is_public=True)
    filename = guide.pdf.name.split('/')[-1]
    response = HttpResponse(guide.pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
