import musicbrainzngs
import musicbrainzngs
from io import BytesIO
import base64
from PIL import Image
import json




try:
    musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")
    get_release = musicbrainzngs.get_release_group_by_id('e9d6e90d-9932-4669-ac1f-9e77a8d1e333', includes=['artists', 'releases'])
    print(get_release)

except musicbrainzngs.WebServiceError as exc:
    print("Something went wrong with the request: %s" % exc)



