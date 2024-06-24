import musicbrainzngs
from musicbrainzngs import *
from io import BytesIO
import base64
from PIL import Image

musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

artist_id = "aedb1c05-5011-40b0-8b44-373be7b1a4d8"
try:
    result = musicbrainzngs.get_artist_by_id(artist_id)
except WebServiceError as exc:
    print("Something went wrong with the request: %s" % exc)
else:
    artist = result["artist"]
    print("name:\t\t%s" % artist["name"])
    print("sort name:\t%s" % artist["sort-name"])

musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

release_id = "c4777169-b451-4256-99e5-e085d8c88672"
cover = musicbrainzngs.get_image_list(release_id)
print(cover)

search_result = musicbrainzngs.search_artists(query="cynic", limit=10)
print(search_result)