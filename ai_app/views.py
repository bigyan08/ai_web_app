from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
# Create your views here.

# decorators= that takes function as an argument and modifies them without changing their functionalities.
# here, using this decorator only user who is logged in can view this page.
# when we try to go this page without loggin in then it should redirect the user to the login page, to do so we need to specify a LOGIN_URL='login' in settings
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt # in this case, there is no need to use csrf token
def generate_blog(request):
    if request.method == 'POST':
        pass
    else:
        return JsonResponse({'error':'Invalid request method'}, status=405) #we dont want user to use GET method.

def user_signup(request):
    if request.method == 'POST':
        username=request.POST['username']
        email=request.POST['email']
        password= request.POST['password']
        repeatPassword = request.POST['repeatPassword']
        if password == repeatPassword:
            try:
                user=User.objects.create_user(username,email,password)
                user.save()
                login(request,user,) #here when the user is created it automatically logs that user in.
                return redirect('/')
            except:
                error_message= 'Error creating your account'
                return render(request,'signup.html', {'error_message':error_message})
        else:
            error_message="Password donot match."
            return render(request,'signup.html', {'error_message':error_message})
    return render(request,'signup.html')


def user_login(request):
    if request.method == 'POST':
        username= request.POST['username']
        password=request.POST['password']
        user=authenticate(request, username=username,password=password)
        if user is not None: # this is simply checking if the user is present in the database.
            login(request,user) # if yes, then just log the user in and redirect him to the home page.
            return redirect('/')
        else: # if there's error then just  display the error to the user 
            error_message='Invalid username or password.'
            return render(request, 'login.html',{'error_message':error_message})
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('/')