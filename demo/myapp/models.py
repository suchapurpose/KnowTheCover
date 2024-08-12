from django.contrib.auth.models import User
from django.db import models
import uuid

class Release(models.Model):
    title = models.CharField(max_length=255)
    cover_image = models.URLField()
    release_id = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
	    return self.title

class ReleaseList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    releases = models.ManyToManyField(Release)
    
    def __str__(self):
	    return self.name
