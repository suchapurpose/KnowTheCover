# views.py
import asyncio
import aiohttp
from aiohttp import ClientSession
from asgiref.sync import sync_to_async

from django.core.cache import cache # for cache

from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from PIL import Image
from .models import TodoItem
import requests
import musicbrainzngs

from .utils import *

from rest_framework.response import Response
from rest_framework.views import APIView

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

# call fetch_cover_image_from_release to fetch image url
def fetch_cover_image_from_artist(artist_id):
    try:
        releases = musicbrainzngs.browse_releases(artist_id, limit=None).get('release-list', [])
        cover_images = []
        count = 0
        seen_titles = set()
        for release in releases:
            if count >= 8:
                break
            title = release.get('title')
            if title in seen_titles:
                continue
            seen_titles.add(title)
            cover_art_archive = release.get('cover-art-archive', {})
            if cover_art_archive.get('artwork') == 'true' and cover_art_archive.get('front') == 'true':
                cover_image_url = cache_by_release(release['id'])
                if cover_image_url:
                    cover_images.append(cover_image_url) # add the url to the cover_images list
                    count += 1
        print(cover_images)
        return cover_images
    except musicbrainzngs.WebServiceError as e:
        print(f"No front cover artwork available for artist {artist_id}: {e}")
        return []
    

# REST testing
    
class CountrySearchView(APIView):
    def get(self, request):
        countryISOA2 = request.GET.get('ISO_A2')
        print(f"Country ISO A2: {countryISOA2}")
        if not countryISOA2:
            return JsonResponse({"error": "Country parameter is missing"}, status=400)

        try:
            result = musicbrainzngs.search_releases(country=countryISOA2, limit=10)
            release_list = result.get('release-list', [])
            print(f"Releases found: {len(release_list)}")

            for release in release_list:
                release_id = release['id']
                cover_images = cache_by_release(release_id=release_id)
                release['cover_images'] = cover_images
                print(f"Release ID: {release_id}, Cover Images: {cover_images}")
            print(release_list)
            return Response(release_list)
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

def cache_by_release(release_id):
    cache_key = f'cover_images_{release_id}'
    cover_images = cache.get(cache_key)

    if not cover_images:
        cover_images = fetch_cover_image_from_release(release_id)
        cache.set(cache_key, cover_images, 60*15) # cache for 15min

    # return JsonResponse({'cover_images': cover_images})
    return cover_images

# fetch cover art using MBID (release_id)
def fetch_cover_image_from_release(release_id):
    try:
        result = musicbrainzngs.get_image_list(release_id)
        image_url = result["images"][0]['thumbnails']
        return image_url.get("250", " ")
        # for image in result["images"]:
        #     if "Front" in image["types"] and image["approved"]:
        #         # thumbnails: 1200, 500, 250, large, small
        #         for size in ["small", "large", "250", "500", "1200"]:
        #             if size in image["thumbnails"]:
        #                 print(image["thumbnails"][size])
        #                 return image["thumbnails"][size]
                    
    except musicbrainzngs.WebServiceError as e:
        print("Something went wrong with the request: %s" % e)
    return []

# REST return each image

class CountrySearchViewEach(APIView):
    def get(self, request):
        countryISOA2 = request.GET.get('ISO_A2')
        print(f"Country ISO A2: {countryISOA2}")
        if not countryISOA2:
            return JsonResponse({"error": "Country parameter is missing"}, status=400)

        try:
            result = musicbrainzngs.search_releases(country=countryISOA2)
            release_list = result.get('release-list', [])
            print(f"Releases found: {len(release_list)}")

            for release in release_list:
                release_id = release['id']
                cover_images = release['cover_images']
                if cover_images:
                    print(f"Release ID: {release_id}, Cover Image: {cover_images}")
                    return Response({'cover_image': cover_images})

            return JsonResponse({"error": "No releases found"}, status=404)   
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
        
def cache_by_release_each(release_id):
    cache_key = f'cover_images_{release_id}'
    cover_images = cache.get(cache_key)

    if not cover_images:
        cover_images = fetch_cover_image_from_release_each(release_id)
        cache.set(cache_key, cover_images, 60*15) # cache for 15min

    # return JsonResponse({'cover_images': cover_images})
    return cover_images
    
# fetch cover art using MBID (release_id)
def fetch_cover_image_from_release_each(release_id):
    try:
        result = musicbrainzngs.get_image_list(release_id)
        for image in result["images"]:
            if "Front" in image["types"] and image["approved"]:
                # thumbnails: 1200, 500, 250, large, small
                for size in ["1200", "500", "250", "large", "small"]:
                    if size in image["thumbnails"]:
                        print(image["thumbnails"][size])
                        return image["thumbnails"][size]
                    
    except musicbrainzngs.WebServiceError as e:
        print("Something went wrong with the request: %s" % e)
    return []