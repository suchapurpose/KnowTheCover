from django.db import models

# Create your models here.
class TodoItem(models.Model):
	title = models.CharField(max_length=200)
	completed = models.BooleanField(default=False)

class CoverArt(models.Model):
	image = models.ImageField(upload_to='cover_arts/')