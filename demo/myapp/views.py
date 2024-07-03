# views.py
import asyncio
import aiohttp
from aiohttp import ClientSession

from django.core.cache import cache # for cache

from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from PIL import Image
from .models import TodoItem
import requests
import musicbrainzngs

from .utils import *

musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

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

def leafletmapajax(request):
    return render(request, "leafletmapajax.html")

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
# metadata and cover art by MBID
def getArtistByID(request):
    artist_id = "aedb1c05-5011-40b0-8b44-373be7b1a4d8"
    release_id = "c4777169-b451-4256-99e5-e085d8c88672"
    artist = fetch_artist_by_id(artist_id)
    image_url = fetch_cover_image_from_release(release_id)
    return render(request, 'getArtistByID.html', {'artist': artist, 'image_url': image_url})
getArtistByID.allow_tags = True

def search(request):
    if request.method == "POST":
        searched = request.POST["searched"]
        search_results = musicbrainzngs.search_artists(searched, limit=4)
        artists = search_results['artist-list']
        
        return render(request, 'search.html', {'searched': searched, 'artists': artists})
    else:
        return render(request, 'search.html', {})
    
def searchAjax(request):
    if request.method == "POST":
        searched = request.POST["searched"]
        if searched:
            search_results = musicbrainzngs.search_artists(searched, limit=4)
            artists = search_results['artist-list']
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'searched': searched, 'artists': artists})
            return JsonResponse({'error': 'Invalid request method'}, status=100)
        else:
            return HttpResponseBadRequest("No search term provided")
    else:
        return render(request, 'search.html',{})

def search_with_cache(request):
    if 'searched' in request.GET:
        searched = request.GET['searched']
        print(f"Search term: {searched}")  # Debug print
        cache_key = f'search_{searched}'
        artists = cache.get(cache_key)

        if not artists:
            search_results = musicbrainzngs.search_artists(searched, limit=10)
            artists = search_results['artist-list']
            cache.set(cache_key, artists, 60*15) # cache for 15min
        
        return render(request, 'search.html', {'searched': searched, 'artists': artists})
    else:
        return render(request, 'search.html', {})
    
# handle fetching cover images by calling fetch_cover_images_from_artists in utils.py    
def fetch_cover_images(request, artist_id):
    cover_images = fetch_cover_image_from_artist(artist_id)
    return JsonResponse({'cover_images': cover_images})

def fetch_cover_images_with_cache(artist_id):
    cache_key = f'cover_images_{artist_id}'
    cover_images = cache.get(cache_key)

    if not cover_images:
        cover_images = fetch_cover_image_from_artist(artist_id)
        cache.set(cache_key, cover_images, 60*15) # cache for 15min

    # return JsonResponse({'cover_images': cover_images})
    return cover_images

def artists_in_country(request):
    country = request.GET.get('ISO_A2')
    if not country:
        return JsonResponse({"error": "Country parameter is missing"}, status=400)

    try:
        result = musicbrainzngs.search_artists(country=country, limit=1)
        artist_list = result['artist-list']

        for artist in artist_list:
            artist_id = artist['id']
            cover_images = fetch_cover_images_with_cache(artist_id=artist_id)
            artist['cover_images'] = cover_images

        return JsonResponse(artist_list, safe=False)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)