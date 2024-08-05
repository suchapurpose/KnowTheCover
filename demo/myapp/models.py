from django.contrib.auth.models import User
from django.db import models

class Release(models.Model):
    title = models.CharField(max_length=255)
    cover_image = models.URLField()
    release_id = models.CharField(max_length=255)

class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    cover_image = models.URLField()
    release_info = models.TextField()
    releases = models.ManyToManyField(Release)
    
def __str__(self):
	return self.title
