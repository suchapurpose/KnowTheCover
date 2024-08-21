import musicbrainzngs
import musicbrainzngs
from io import BytesIO
import base64
from PIL import Image
import json




try:
    musicbrainzngs.set_useragent("CoverArtMap", "0.1", "terrylau563@mgmail.com")
    release_types = musicbrainzngs.VALID_RELEASE_TYPES
    print(release_types)
    search_release = musicbrainzngs.search_releases(arid='aedb1c05-5011-40b0-8b44-373be7b1a4d8', type='album', limit=10, strict=True)
    seen = set()
    for release in search_release['release-list']:
        if not release['title'] in seen:
            seen.add(release['title'])

    print(seen)


except musicbrainzngs.WebServiceError as exc:
    print("Something went wrong with the request: %s" % exc)



