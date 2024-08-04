from django.contrib.auth.models import User
from django.db import models

class Collection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    cover_image = models.URLField()
    release_info = models.TextField()
    
def __str__(self):
	return self.title