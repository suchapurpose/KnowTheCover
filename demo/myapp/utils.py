import musicbrainzngs
from musicbrainzngs import *

# fetch data using MBID (artist id)
def fetch_artist_by_id(artist_id):
    musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

    try:
        result = musicbrainzngs.get_artist_by_id(artist_id)
    except WebServiceError as exc:
        print("Something went wrong with the request: %s" % exc)
    else:
        artist = result["artist"]
        return artist  
        
# fetch cover art using MBID (release_id)
def fetch_cover_image(release_id):
    try:
        result = musicbrainzngs.get_image_list(release_id)
        for image in result["images"]:
            if "Front" in image["types"] and image["approved"]:
                # thumbnails: 1200, 500, 250, large, small
                return image["thumbnails"]["500"]
    except WebServiceError as exc:
        print("Something went wrong with the request: %s" % exc)
    return None

