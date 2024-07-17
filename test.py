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

# musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")

# release_id = "c4777169-b451-4256-99e5-e085d8c88672"
# release_detail = musicbrainzngs.get_release_by_id(release_id)
# print(release_detail)
# cover = musicbrainzngs.get_image_list(release_id)
# print(cover)

# search_result = musicbrainzngs.search_artists(query="cynic", limit=1)
# json_output = json.dumps(search_result, indent=2)
# print(search_result)
# with open('search_result.json', 'w') as json_file:
#     json_file.write(json_output)
# print("")

# # i suppose its using ISO_A2?
# by_country = musicbrainzngs.search_releases(query=f'country:{"GB"}', limit=4, offset=1)
# releases = by_country['release-list']
# release_detail = musicbrainzngs.get_release_by_id(release_id)
# print(by_country)

release_id = "a0ad316d-89a2-4f49-b439-8296ca98be01"
image_list = musicbrainzngs.get_image_list(release_id)
print(image_list)

