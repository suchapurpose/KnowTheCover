import musicbrainzngs

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

# fetch cover art using MBID (artist_id)
def fetch_cover_image_from_artist(artist_id):
    try:
        releases = musicbrainzngs.browse_releases(artist_id, limit=5).get('release-list', [])
        cover_images = []
        count = 0
        for release in releases:
            if count >= 3:
                break
            cover_art_archive = release.get('cover-art-archive', {})
            if cover_art_archive.get('artwork') == 'true' and cover_art_archive.get('front') == 'true':
                cover_image_url = fetch_cover_image_from_release(release['id'])
                if cover_image_url:
                    # add the url to the cover_images list
                    cover_images.append(cover_image_url)
                    # increment
                    count += 1
        #return the cover_images list
        print(cover_images)
        return cover_images
    except musicbrainzngs.WebServiceError as e:
        print(f"No front cover artwork available for artist {artist_id}: {e}")
        return []