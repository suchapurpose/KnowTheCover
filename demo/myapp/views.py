from django.shortcuts import render, HttpResponse
from PIL import Image
from .models import TodoItem
import requests
import musicbrainzngs
from musicbrainzngs import *
from io import BytesIO
import base64


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

# musicbrainzngs API
# regular data
def getArtistByID(request):
    musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

    artist_id = "aedb1c05-5011-40b0-8b44-373be7b1a4d8"
    release_id = "c4777169-b451-4256-99e5-e085d8c88672"

    try:
        result = musicbrainzngs.get_artist_by_id(artist_id)

    except WebServiceError as exc:
        print("Something went wrong with the request: %s" % exc)
    else:
        artist = result["artist"]
        cover_data = musicbrainzngs.get_image(release_id, "front")
        decoded_cover = base64.b64decode(cover_data)
        # pillow_image = Image.frombytes("RGB", (50, 50), decoded_cover)
        return render(request, 'getArtistByID.html', {'artist': artist, 'cover': cover_data})
    
getArtistByID.allow_tags = True