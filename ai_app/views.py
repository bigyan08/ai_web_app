from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from pytube import YouTube
from django.conf import settings
import os
import assemblyai as aai
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Create your views here.

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

from pytube import exceptions

def download_audio(link):
    try:
        yt = YouTube(link)
        print(f"Successfully accessed video: {yt.title}")

        # Filter for audio streams
        video = yt.streams.filter(only_audio=True).first()
        if not video:
            print("No audio streams found.")
            return None

        out_file = video.download(output_path=settings.MEDIA_ROOT)
        print(f"Audio downloaded to: {out_file}")

        # Renaming the file to mp3
        base, ext = os.path.splitext(out_file)
        new_file = base + ".mp3"
        os.rename(out_file, new_file)
        print(f"Audio file renamed to: {new_file}")

        return new_file
    except exceptions.VideoUnavailable:
        print("The video is unavailable.")
    except exceptions.LiveStreamError:
        print("This video is a live stream and cannot be downloaded.")
    except exceptions.RegexMatchError:
        print("The URL provided did not match any available streams.")
    except Exception as e:
        print(f"Error downloading audio: {e}")
    return None



def get_transcription(link):
    audio_file = download_audio(link)
    if not audio_file:
        raise Exception("Audio file was not created.")
    aai.settings.api_key = os.environ["API_KEY_ASSEMBLYAI"]
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)
    return transcript.text


def generate_blog_from_transcription(transcription):
    genai.configure(api_key=os.environ['API_KEY_GENAI'])  # Use environment variable
    prompt = f'Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but don’t make it look like a YouTube video, make it look like a proper blog article: \n\n {transcription}\n\nArticle:'
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text

@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt 
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) 
            yt_link = data['link'] 
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid Data Sent'}, status=400)
        
        title = yt_title(yt_link)
        transcription = get_transcription(yt_link)
        if not transcription:
            return JsonResponse({'error': "Transcript process failed!"}, status=500)
        
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': 'Failed to generate blog article'}, status=500)

        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating your account'
                return render(request, 'signup.html', {'error_message': error_message})
        else:
            error_message = "Password do not match."
            return render(request, 'signup.html', {'error_message': error_message})
    return render(request, 'signup.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = 'Invalid username or password.'
            return render(request, 'login.html', {'error_message': error_message})
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('/')
