import musicbrainzngs
import musicbrainzngs
from io import BytesIO
import base64
from PIL import Image
import json

musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

artist_id = "aedb1c05-5011-40b0-8b44-373be7b1a4d8"
try:
    result = musicbrainzngs.search_artists(query="title fight", limit=1)
    for artist in result["artist-list"]:
        print(artist["name"])
        releases = musicbrainzngs.browse_releases(artist=artist["id"], limit=1)
        print(releases)
        get_release = musicbrainzngs.get_release_by_id('5890a3cd-bf8b-4f43-98d2-008e11c65e43', includes=['artists', 'recordings', 'release-groups', 'labels'])
        print(get_release)

except musicbrainzngs.WebServiceError as exc:
    print("Something went wrong with the request: %s" % exc)



