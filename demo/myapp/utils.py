# utils.py
import musicbrainzngs # music database
import aiohttp # to make asynchronous requests
import asyncio 


# fetch data using MBID (artist id)
def fetch_artist_by_id(artist_id):
    musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

    try:
        result = musicbrainzngs.get_artist_by_id(artist_id)
    except musicbrainzngs.WebServiceError as exc:
        print("Something went wrong with the request: %s" % exc)
    else:
        artist = result["artist"]
        return artist  
        
# fetch cover art using MBID (release_id)
def fetch_cover_image_from_release(release_id):
    try:
        result = musicbrainzngs.get_image_list(release_id)
        for image in result["images"]:
            if "Front" in image["types"] and image["approved"]:
                # thumbnails: 1200, 500, 250, large, small
                for size in ["small", "large", "250", "500", "1200"]:
                    if size in image["thumbnails"]:
                        return image["thumbnails"][size]
    except musicbrainzngs.WebServiceError as e:
        print("Something went wrong with the request: %s" % e)
    return None

# async fetch cover art using MBID (release_id)
async def fetch_cover_image_from_release_async(session, release_id):
    url = musicbrainzngs.get_image_list(release_id)
    async with session.get(url) as response:
        if response.status == 200: # check if the response is relevant
            result = await response.json() # parse the JSON response
            for image in result["images"]:
                if "Front" in image["types"] and image["approved"]:
                    for size in ["small", "large", "250", "500", "1200"]:
                        if size in image["thumbnails"]:
                            return image["thumbnails"][size]
    return None

# fetch cover art using MBID (artist_id)
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
                cover_image_url = fetch_cover_image_from_release(release['id'])
                if cover_image_url:
                    cover_images.append(cover_image_url) # add the url to the cover_images list
                    count += 1
        print(cover_images)
        return cover_images
    except musicbrainzngs.WebServiceError as e:
        print(f"No front cover artwork available for artist {artist_id}: {e}")
        return []
    
async def fetch_cover_image_from_artist_async(session, artist_id):
    try:
        releases = musicbrainzngs.browse_releases(artist_id, limit=None).get('release-list', [])
        async_tasks = [] # async tasks list
        for release in releases:
            cover_art_archive = release.get('cover-art-archive', {})
            if cover_art_archive.get('artwork') == 'true' and cover_art_archive.get('front') == 'true':
                async_tasks.append(fetch_cover_image_from_release_async(session, release['id']))

        # run all tasks concurrently and wait for time to complete
        cover_images = await asyncio.gather(*async_tasks)
        return [img for img in cover_images if img] # filter out none value
    except musicbrainzngs.WebServiceError as e:
        print(f"No front cover artwork available for artist {artist_id}: {e}")
        return []