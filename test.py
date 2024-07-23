import musicbrainzngs
import musicbrainzngs
from io import BytesIO
import base64
from PIL import Image
import json

musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

artist_id = "aedb1c05-5011-40b0-8b44-373be7b1a4d8"
try:
    result = musicbrainzngs.search_artists(query="title fight", limit=2)
    for artist in result["artist-list"]:
        print(artist["name"])
        releases = musicbrainzngs.browse_releases(artist=artist["id"], limit=10)
        print(json.dumps(releases, indent=4))
        for release in releases["release-list"]:
            print(release["title"])
            print(release["id"])
            cover_art_archive = release.get("cover-art-archive", {})
            if cover_art_archive.get("artwork") == "true" and cover_art_archive.get("front") == "true":
                image = musicbrainzngs.get_image_list(release["id"])
                image_url = image["images"][0]["image"]
                # print(image_url)
except musicbrainzngs.WebServiceError as exc:
    print("Something went wrong with the request: %s" % exc)



