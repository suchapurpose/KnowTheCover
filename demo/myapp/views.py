# views.py
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.views.decorators.gzip import gzip_page

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse
import musicbrainzngs

import json

from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth.decorators import login_required
from .models import ReleaseList, Release
from .forms import ReleaseListForm
from .utils import COUNTRY_CODES

import logging

# set user agent for musicbrainzngs
musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

# Map View ================================================================================================
@gzip_page # compress the response
def leafletmapajax(request):
    # fetch valid release types in MusicBrainz
    valid_release_types = musicbrainzngs.VALID_RELEASE_TYPES
    return render(request, "leafletmapajax.html", {'valid_release_types': valid_release_types})

# Collection Views ========================================================================================
@login_required
def collections(request):
    # get all collections for the current user
    collections = ReleaseList.objects.filter(user=request.user)
    return render(request, "collections.html", {'collections': collections})

@login_required
def create_collection(request):
    if request.method == 'POST':
        form = ReleaseListForm(request.POST)
        # check if the form is valid
        if form.is_valid():
            collection = form.save(commit=False)
            collection.user = request.user
            collection.save()
            return JsonResponse({'success': True, 'redirect_url': reverse('collections')}, status=201)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)    
    else:
        form = ReleaseListForm()
    return render(request, 'create_collection.html', {'form': form})

@login_required
def collection_detail(request, collection_id):
    # get the collection by id
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
def get_user_collections(request):
    lists = ReleaseList.objects.filter(user=request.user)
    # return a list of dictionaries with collection name and id
    list_data = [{'name': list.name, "id": list.id } for list in lists]
    return JsonResponse({'collections': list_data})

@login_required
def add_release_to_collection(request):
    if request.method == 'POST':
        try:
            # get the JSON data from the request body
            data = json.loads(request.body)
            release_data = data.get('release', {})
            release_id = release_data.get('id')
            print(f"Release ID: {release_id}")
            collection_id = data.get('collection_id')
            print(f"Collection ID: {collection_id}")

            collection = get_object_or_404(ReleaseList, id=collection_id, user=request.user)
            # create a new release or get an existing release
            release, created = Release.objects.get_or_create(
                release_id=release_id,
                defaults={
                    'title': release_data.get('title'), 
                    'cover_image': release_data.get('cover_image'), 
                    'release_data': release_data
                }
            )
            print(f"Release: {release}")
            collection.releases.add(release)
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            print("JSONDecodeError: Invalid JSON")
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Exception: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)

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

# Release Detail View ======================================================================================

def release_detail(request, release_id):
    try:
        release = Release.objects.get(release_id=release_id)
        # get all collections for the current user if authenticated
        collections = ReleaseList.objects.filter(user=request.user) if request.user.is_authenticated else None
        if release:
            return render(request, 'release_detail.html', {'release': release, 'collections': collections})

    # if the release is not found, create a new release
    except Release.DoesNotExist:
        release = None
        if request.method == 'POST':
            try:
                # get the JSON data from the request body
                data = json.loads(request.body)
                release_data = data.get('release', {})
                title = release_data.get('title')
                release_id = release_data.get('id')
                cover_image = release_data.get('cover_image')

                release, created = Release.objects.get_or_create(
                    release_id=release_id,
                    defaults={
                        'title': title, 
                        'cover_image': cover_image, 
                        'release_data': release_data
                    }
                )
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
    
    return render(request, 'release_detail.html', {'release': release, 'collections': collections})
        
# Country Search ================================================================================================
class CountrySearchView(APIView):
    def get(self, request):
        # get country code from query string
        countryISOA2 = request.GET.get('ISO_A2')
        if not countryISOA2:
            return JsonResponse({"error": "Country parameter is missing"}, status=400)
        
        if countryISOA2 not in COUNTRY_CODES:
            return JsonResponse({"error": "Invalid country code"}, status=400)

        # get selected release type from query string
        selected_release_type = request.GET.get('selected_release_type', '')
        limit = 12 # number of releases per page
        offset = request.session.get('offset', 0)
        fetch_count = 0

        try:
            all_releases_with_images = []
            while len(all_releases_with_images) < limit:
                # search for releases by country
                result = musicbrainzngs.search_releases(
                    country=countryISOA2, 
                    limit=100, 
                    offset=offset, 
                    type=selected_release_type
                )
                release_list = result.get('release-list', [])

                if not release_list:
                    break  # if no more releases to fetch

                for release in release_list:
                    fetch_count += 1
                    release_id = release['id']
                    release_title = release['title']
                    cover_image = cache_by_release(release_id=release_id)
                    if cover_image:
                        release['cover_image'] = cover_image
                        all_releases_with_images.append(flatten_release_data(release))
                    if len(all_releases_with_images) == limit:
                        break  # Stop if we have enough releases with images
                offset += fetch_count
                new_list = all_releases_with_images.copy()
            all_releases_with_images.clear() # clear the list

            # store the offset in the session
            request.session['offset'] = offset

            # return the response
            response_data = {
                'releases': new_list,
                'fetch_count': fetch_count,
                'offset': offset,
            }
            return JsonResponse(response_data, safe=False)
        except musicbrainzngs.WebServiceError as e:
            return JsonResponse({"error": str(e)}, status=500)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

# fetch cover art =================================================================================================
# check and cache cover images by release ID
def cache_by_release(release_id):
    # check if the cover image is already cached
    cache_key = f'cover_image_{release_id}'
    cover_image = cache.get(cache_key)
    if not cover_image:
        cover_image = fetch_cover_image_from_release(release_id)
        cache.set(cache_key, cover_image, 60*15) # cache for 15 minutes

    return cover_image

# fetch cover art using MBID (release_id)
def fetch_cover_image_from_release(release_id):
    try:
        # get the image list by release id
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

# Artist Search ================================================================================================
class ArtistSearchView(APIView):
    def get(self, request):
        query = request.GET.get('query')
        if not query:
            return Response({"error": "No search term provided"}, status=400)
        
        selected_release_type = request.GET.get('selected_release_type', '').split(',')
        page_number = request.GET.get('page', 1)
        offset = int(request.GET.get('offset', 0))
        limit = 2

        try:
            artist_list_for_page = []
            # search for artists by keyword
            result = musicbrainzngs.search_artists(query, limit=10, offset=offset)
            artist_list = result.get('artist-list', [])
            print(f"Artists found: {len(artist_list)}")
            for artist in artist_list:
                if len(artist_list_for_page) == limit:
                    break
                # fetch cover image for the artist
                release_info = fetch_cover_image_from_artist(artist, selected_release_type)
                artist['release_info'] = release_info
                artist_list_for_page.append(artist)

            copy_list = artist_list_for_page.copy()
            artist_list_for_page.clear()

            # paginate the artist list
            paginator = Paginator(copy_list, limit)

            try:
                page_obj = paginator.page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(paginator.num_pages)
            except EmptyPage:
                page_obj = paginator.page(paginator.num_pages)

            response_data = {
                'artist_list': list(page_obj),
                'current_page': page_obj.number,
                'total_items': paginator.count,
            }

            return JsonResponse(response_data, safe=False)
        except musicbrainzngs.WebServiceError as e:
            return Response({"error": str(e)}, status=500)
        
# call fetch_cover_image_from_release to fetch image url
def fetch_cover_image_from_artist(artist, selected_release_type):
    try:
        artist_id = artist['id']
        cache_key = f'cover_image_{artist_id}_{selected_release_type}'
        release_list_with_image = cache.get(cache_key)

        if release_list_with_image is None:
            # search for releases by artist id
            releases = musicbrainzngs.search_releases(arid=artist_id, limit=None, primarytype=selected_release_type)
            release_list = releases.get('release-list', [])
            release_list_with_image = []
            # store release group id to avoid duplicates
            seen_release_groups = set()
            for release in release_list:
                release_id = release['id']
                release_group = release['release-group']['id']
                if release_group in seen_release_groups:
                    continue # skip releases in the same release group
                cover_image_url = fetch_cover_image_from_release(release_id)
                if cover_image_url:
                    release['cover_image'] = cover_image_url
                    release_list_with_image.append(flatten_release_data(release))
                    seen_release_groups.add(release_group) # add unsaved release group id
            cache.set(cache_key, release_list_with_image, 60*15)

        return release_list_with_image
    except musicbrainzngs.WebServiceError as e:
        return []
    
# literate over the keys and values in release_data
def flatten_release_data(release):
    if 'release_data' in release:
        for key, value in release['release_data'].items():
            release[key] = value
        # remove the nested release_data key
        del release['release_data']
    return release