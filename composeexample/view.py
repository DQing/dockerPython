from django.shortcuts import render


def index(request):
    context = {'hello': 'Hello World!'}
    return render(request, 'index.html', context)


def hello(request):
    context = {'hello': 'Hello World!'}
    return render(request, 'user.html', context)
