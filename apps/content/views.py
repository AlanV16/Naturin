from django.shortcuts import render

def bella_durmiente_detail(request):
    return render(request, 'content/explore_bella_durmiente.html')

def cueva_lechuzas_detail(request):
    return render(request, 'content/explore_cueva_lechuzas.html')

def laguna_milagros_detail(request):
    return render(request, 'content/explore_laguna_milagros.html')

def jardin_botanico_detail(request):
    return render(request, 'content/explore_jardin_botanico.html')

def cascada_leon_detail(request):
    return render(request, 'content/explore_cascada_leon.html')

def cueva_pavas_detail(request):
    return render(request, 'content/explore_cueva_pavas.html')

def catarata_santa_carmen_detail(request):
    return render(request, 'content/explore_catarata_santa_carmen.html')

def catarata_san_miguel_detail(request):
    return render(request, 'content/explore_catarata_san_miguel.html')

def zoocriadero_detail(request):
    return render(request, 'content/explore_zoocriadero.html')

def rio_huallaga_detail(request):
    return render(request, 'content/explore_rio_huallaga.html')
