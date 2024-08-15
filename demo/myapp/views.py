# views.py
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache # for cache

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import musicbrainzngs

from .utils import *
import json

from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth.decorators import login_required
from .models import ReleaseList, Release
from .forms import ReleaseListForm

import logging

# set user agent for musicbrainzngs
musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

# Create your views here.

# simple hello world function
# def home(request)
#   return HttpResponse("Hello World!")

def home(request):
    return render(request, "home.html")

def leafletmapajax(request):
    return render(request, "leafletmapajax.html")

@login_required
def collections(request):
    collections = ReleaseList.objects.filter(user=request.user)
    return render(request, "collections.html", {'collections': collections})

@login_required
def create_collection(request):
    if request.method == 'POST':
        form = ReleaseListForm(request.POST)
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()
            return redirect('collections')
    else:
        form = ReleaseListForm()
    return render(request, 'create_collection.html', {'form': form})

@login_required
def get_user_collections(request):
    lists = ReleaseList.objects.filter(user=request.user)

    print(lists)
    list_data = [{'name': list.name, "id": list.id } for list in lists]
    return JsonResponse({'collections': list_data})

@login_required
def add_release_to_collection(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(f"Data: {data}")
            release_data = data.get('release', {})
            print(f"Release data: {release_data}")
            release_id = release_data.get('id')
            print(f"Release ID: {release_id}")
            collection_id = data.get('collection_id')
            print(f"Collection ID: {collection_id}")

            collection = get_object_or_404(ReleaseList, id=collection_id, user=request.user)
            print(f"Collection: {collection}")
            release, created = Release.objects.get_or_create(
                release_id=release_id,
                defaults={
                    'title': release_data.get('title'), 
                    'cover_image': release_data.get('cover_image'), 
                    'release_data': release_data
                }
            )
            collection.releases.add(release)
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

@login_required
def collection_detail(request, collection_id):
    collection = get_object_or_404(ReleaseList, id=collection_id, user=request.user)
    return render(request, 'collection_detail.html', {'collection': collection})

@login_required
def delete_collection(request, collection_id):
    collection = get_object_or_404(ReleaseList, id=collection_id, user=request.user)
    if request.method == 'POST':
        collection.delete()
        return redirect('collections')
    return render(request, 'delete_collection.html', {'collection': collection})

@login_required
def delete_release_from_collection(request, collection_id, release_id):
    collection = get_object_or_404(ReleaseList, id=collection_id, user=request.user)
    release = get_object_or_404(Release, release_id=release_id)
    if request.method == 'POST':
        collection.releases.remove(release)
        # check if the release is in other collections
        release_in_other_collections = ReleaseList.objects.filter(releases=release).exists()
        # if not, delete the release
        if not release_in_other_collections:
            release.delete()
        return redirect('collection_detail', collection_id=collection_id)
    return render(request, 'delete_release_from_collection.html', {'collection_id': collection_id, 'release_id': release_id, 'release': release})

logger = logging.getLogger(__name__)

def release_detail(request, release_id):
    try:
        release = Release.objects.get(release_id=release_id)
    except Release.DoesNotExist:
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                print(f"Data: {data}")
                release_data = data.get('release', {})
                print(f"Release data: {release_data}")
                title = release_data.get('title')
                print(f"Title: {title}")
                release_id = release_data.get('id')
                print(f"Release ID: {release_id}")
                cover_image = release_data.get('cover_image')
                print(f"Cover image: {cover_image}")

                release = Release.objects.create(
                    release_id=release_id,
                    title=title,
                    cover_image=cover_image,
                    release_data=release_data
                )
                print(f"Release: {release}")
                return JsonResponse({'success': True, 'release_id': release_id})
            except json.JSONDecodeError:
                print("JSONDecodeError: Invalid JSON")
                return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
            except Exception as e:
                print(f"Exception: {str(e)}")
                return JsonResponse({'success': False, 'error': str(e)}, status=500)
        else:
            print("Error: Release not found and request method is not POST")
            return JsonResponse({'success': False, 'error': 'Release not found'}, status=404)

    for key, value in release.release_data.items():
        logger.info(f"Key: {key}, Value: {value}")
    return render(request, 'release_detail.html', {'release': release})
    
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
        limit = 12 # Number of releases per page
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
                        all_releases_with_images.append(flatten_release_data(release))
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
            print(f"Limit: {limit}")
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
                'current_page': page_obj.number,
                'total_items': paginator.count,
            }
            return JsonResponse(response_data, safe=False)
        except Exception as e:
            print(f"Error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

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
        if "1200" in image_url:
            print(image_url["1200"])
            return image_url.get("1200", " ")                   
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
        
        page_number = request.GET.get('page', 1)
        offset = int(request.GET.get('offset', 0))
        print(f"offset: {offset}")
        limit = 2

        try:
            artist_list_for_page = []
            result = musicbrainzngs.search_artists(query, limit=10, offset=offset)
            artist_list = result.get('artist-list', [])
            print(f"Artists found: {len(artist_list)}")
            for artist in artist_list:
                if len(artist_list_for_page) == limit:
                    break
                artist_id = artist['id']
                artist_name = artist['name']
                print(f"Artist: {artist_name} ({artist_id})")
                release_info = fetch_cover_image_from_artist(artist)
                artist['release_info'] = release_info
                artist_list_for_page.append(artist)

            copy_list = artist_list_for_page.copy()
            artist_list_for_page.clear()

            paginator = Paginator(copy_list, limit)
            print(f"total pages: {paginator.num_pages}")

            try:
                page_obj = paginator.page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(paginator.num_pages)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)
                print(f"Page {page_number} is out of range")


            response_data = {
                'artist_list': list(page_obj),
                'current_page': page_obj.number,
                'total_items': paginator.count,
            }

            return JsonResponse(response_data, safe=False)
        except musicbrainzngs.WebServiceError as e:
            return Response({"error": str(e)}, status=500)
        
# call fetch_cover_image_from_release to fetch image url
def fetch_cover_image_from_artist(artist):
    try:
        artist_id = artist['id']
        print(f"Artist ID: {artist_id}")
        releases = musicbrainzngs.search_releases(arid=artist_id, limit=None)
        release_list =releases.get('release-list', [])
        print(f"Releases found: {release_list}")
        release_list_with_image = []
        count = 0
        seen_titles = set()
        for release in release_list:
            print(f"Release: {release}")
            release_id = release['id']
            title = release.get('title')
            if title in seen_titles:
                continue # skip duplicated titles
            seen_titles.add(title) # add new titles
            cover_image_url = fetch_best_cover_image(release_id)
            if cover_image_url:
                release['cover_image'] = cover_image_url
                release_list_with_image.append(flatten_release_data(release))
        print(f"Release list: {release_list_with_image}")
        return release_list_with_image
    except musicbrainzngs.WebServiceError as e:
        print(f"No front cover artwork available for artist {artist_id}: {e}")
        return []
    
def flatten_release_data(release):
    if 'release_data' in release:
        for key, value in release['release_data'].items():
            release[key] = value
        del release['release_data']
    return release