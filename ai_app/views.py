from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
from dotenv import load_dotenv
import openai

# Create your views here.

def yt_title(link):
    yt= YouTube(link)
    title=yt.title
    return title

def download_audio(link):
    yt=YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)
    base,ext= os.path.splitext(out_file) #separating the name of the file to base and ext, i.e is base name and extension name
    new_file = base + ".mp3" # then creating a new file which has base name but mp3 extension
    os.rename(out_file,new_file)
    return new_file

def get_transcription(link):
    audio_file=download_audio(link)
    aai.settings.api_key=os.getenv("ASSEMBLY_API_KEY")

    transcriber = aai.Transcriber()
    transcript=transcriber.transcribe(audio_file)
    return transcriber.text

def generate_blog_from_transcription(transcription):
    openai.api_key = os.getenv("OPENAI_KEY")
    prompt = f'Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but donot make it look like a youtube video, make it look like a proper blog article: \n\n {transcription}\n\nArticle:'
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )
    generated_content= response.choices[0].text.strip() 
    # here if it was just response, then it would return in a dictionary format. choices[0] takes first choice, strip() strips the text of the first choice.
    #response.choices: Accesses the list of choices (possible generated completions).
    # response.choices[0]: Accesses the first completion (choice) in the list.
    # response.choices[0].text: Extracts the raw generated text from the first completion.
    # response.choices[0].text.strip(): Removes any extra spaces, newlines, or tabs from the beginning and end of the generated text.
    return generated_content



# decorators= that takes function as an argument and modifies them without changing their functionalities.
# here, using this decorator only user who is logged in can view this page.
# when we try to go this page without loggin in then it should redirect the user to the login page, to do so we need to specify a LOGIN_URL='login' in settings
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt # in this case, there is no need to use csrf token
def generate_blog(request):
    if request.method == 'POST':
        try:
           data= json.loads(request.body) 
           yt_link = data['link'] 
        except(KeyError,json.JSONDecodeError):
            return JsonResponse({'error':'Invalid Data Sent'}, status=400)
        

        #get title
        title= yt_title(yt_link)

        #get transcript
        transcription=get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error':"Transcript process failed!"},status=500)

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