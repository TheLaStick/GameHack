from django.shortcuts import render

# Create your views here.

def play(request):
    if request.method == 'GET':

        return render(request, '')
    if request.method == 'POST':
        button1 = request.POST.get('')
        button2 = request.POST.get('')

        return render(request, '')


