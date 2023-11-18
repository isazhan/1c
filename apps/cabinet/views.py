from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(cabinet)
        else:
            return render(request, 'cabinet/login.html')
    else:
        return render(request, 'cabinet/login.html')
    

def cabinet(request):
    return render(request, 'cabinet.html')