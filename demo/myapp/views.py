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

# MusicBrainz
# lookup:   /<ENTITY_TYPE>/<MBID>?inc=<INC>
# browse:   /<RESULT_ENTITY_TYPE>?<BROWSING_ENTITY_TYPE>=<MBID>&limit=<LIMIT>&offset=<OFFSET>&inc=<INC>
# search:   /<ENTITY_TYPE>?query=<QUERY>&limit=<LIMIT>&offset=<OFFSET>

# lookup
def searchWithID(request):
    url = f'https://musicbrainz.org/ws/2/artist/aedb1c05-5011-40b0-8b44-373be7b1a4d8?inc=aliases&fmt=json'
    response = requests.get(url)
    data = response.json()
    return render(request, 'searchWithID.html', {'data': data})

# browse
