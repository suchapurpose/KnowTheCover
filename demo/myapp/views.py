from django.shortcuts import render, HttpResponse
from .models import TodoItem
import requests

# Create your views here.

# simple hello world function
# def home(request)
#   return HttpResponse("Hello World!")

def home(request):
    return render(request, "home.html")

def todos(request):
    items = TodoItem.objects.all()
    return render(request, "todos.html", {"todos": items})

def leafletmap(request):
    return render(request, "leafletmap.html")

def apitest(request):
    response = requests.get('https://musicbrainz.org/ws/2/area/45f07934-675a-46d6-a577-6f8637a411b1?inc=aliases')
    data = response.json()
    return render(request, "apitest.html", {"data": data})