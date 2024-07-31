# views.py
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache # for cache

from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest, StreamingHttpResponse
import json
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

def leafletmapajax(request):
    return render(request, "leafletmapajax.html")

# MusicBrainz
# lookup:   /<ENTITY_TYPE>/<MBID>?inc=<INC>
# browse:   /<RESULT_ENTITY_TYPE>?<BROWSING_ENTITY_TYPE>=<MBID>&limit=<LIMIT>&offset=<OFFSET>&inc=<INC>
# search:   /<ENTITY_TYPE>?query=<QUERY>&limit=<LIMIT>&offset=<OFFSET>

# musicbrainzngs API
# metadata and cover art by MBID   
    
# Country Search================================================================================================
class CountrySearchView(APIView):
    def get(self, request):
        # ensure the existence of the ISO_A2 country parameter
        countryISOA2 = request.GET.get('ISO_A2')
        print(f"Country ISO A2: {countryISOA2}")
        if not countryISOA2:
            return JsonResponse({"error": "Country parameter is missing"}, status=400)

        page_number = int(request.GET.get('page', 1))
        limit = 10 # Number of releases per page
        offset = request.session.get('offset', 0)
        fetch_count = 0

        # main function
        try:
            all_releases_with_images = []
            # fetch cover images for each release
            while len(all_releases_with_images) < limit:
                result = musicbrainzngs.search_releases(country=countryISOA2, limit=100, offset=offset)
                release_list = result.get('release-list', [])
                print(f"Releases found: {len(release_list)}")
                print(f"1st release: {release_list[0]}")

                if not release_list:
                    break  # if no more releases to fetch

                for release in release_list:
                    fetch_count += 1
                    release_id = release['id']
                    release_title = release['title']
                    print(f"Release title: {release_title}")
                    cover_image = cache_by_release(release_id=release_id)
                    if cover_image:
                        release['cover_image'] = cover_image
                        all_releases_with_images.append(release)
                    if len(all_releases_with_images) == limit:
                        print(f"Fetch count: {fetch_count}")
                        break  # Stop if we have enough releases with images
                offset += fetch_count
                print(f"Offset: {offset}")
                new_list = all_releases_with_images.copy()
            all_releases_with_images.clear() # clear the list
            print(f"all_releases_with_images length: {len(all_releases_with_images)}")
            print(f"new_list length: {len(new_list)}")

            request.session['offset'] = offset

            # use Django Paginator
            paginator = Paginator(new_list, limit)
            try:
                print(f"Page number: {page_number}")
                page_obj = paginator.page(page_number)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
                print(f"Page {page_number} is out of range")
            except PageNotAnInteger:
                page_obj = paginator.page(paginator.num_pages)
                print(f"Page number is not an integer, default to page 1")
            # return the response
            response_data = {
                'releases': list(page_obj),
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'total_items': paginator.count,
            }
            return JsonResponse(response_data, safe=False)
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

# for streaming response
def generate_cover_image(release_list):
    for release in release_list:
        release_id = release['id']
        cover_image = cache_by_release(release_id)
        if cover_image:
            yield f"data: {{'cover_image': cover_image}}\n\n".encode('utf-8')
        else:
            yield f"data: {{'cover_image': None}}\n\n".encode('utf-8')

# check and cache cover images by release ID
def cache_by_release(release_id):
    cache_key = f'cover_image_{release_id}'
    cover_image = cache.get(cache_key)
    if not cover_image:
        cover_image = fetch_cover_image_from_release(release_id)
        cache.set(cache_key, cover_image, 60*15) # cache for 15min

    return cover_image

# fetch cover art using MBID (release_id)
def fetch_cover_image_from_release(release_id):
    try:
        result = musicbrainzngs.get_image_list(release_id)
        image_url = result["images"][0]['thumbnails']
        if "250" in image_url:
            print(image_url["250"])
            return image_url.get("250", " ")                   
    except musicbrainzngs.WebServiceError as e:
        print("Something went wrong with the request: %s" % e)
    return []

# fetch cover image with highest resolution
def fetch_best_cover_image(release_id):
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

# Artist Search================================================================================================
class ArtistSearchView(APIView):
    def get(self, request):
        query = request.GET.get('query')
        if not query:
            return Response({"error": "No search term provided"}, status=400)

        try:
            result = musicbrainzngs.search_artists(query, limit=10)
            artist_list = result.get('artist-list', [])
            for artist in artist_list:
                artist_id = artist['id']
                artist_name = artist['name']
                print(f"Artist: {artist_name} ({artist_id})")
                release_info = fetch_cover_image_from_artist(artist_id)
                artist['release_info'] = release_info

            page_number = request.GET.get('page', 1)
            paginator = Paginator(artist_list, 3)

            try:
                page_obj = paginator.page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            response_data = {
                'artist_list': list(page_obj),
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'total_items': paginator.count,
            }

            return JsonResponse(response_data, safe=False)
        except musicbrainzngs.WebServiceError as e:
            return Response({"error": str(e)}, status=500)
        
# call fetch_cover_image_from_release to fetch image url
def fetch_cover_image_from_artist(artist_id):
    try:
        releases = musicbrainzngs.browse_releases(artist_id, limit=None).get('release-list', [])
        release_list = []
        count = 0
        seen_titles = set()
        for release in releases:
            if count >= 6:
                count = 0
                break
            title = release.get('title')
            if title in seen_titles:
                continue # skip duplicated titles
            seen_titles.add(title) # add new titles
            cover_art_archive = release.get('cover-art-archive', {})
            if cover_art_archive.get('artwork') == 'true' and cover_art_archive.get('front') == 'true':
                cover_image_url = cache_by_release(release['id'])
                if cover_image_url:
                    release_info = {
                        'title': title,
                        'cover_image': cover_image_url,
                    }
                    release_list.append(release_info)
                    count += 1
        print(release_list)
        return release_list
    except musicbrainzngs.WebServiceError as e:
        print(f"No front cover artwork available for artist {artist_id}: {e}")
        return []