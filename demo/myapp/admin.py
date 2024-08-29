from django.contrib import admin
from .models import ReleaseList, Release

# Register your models here.
admin.site.register(ReleaseList)
admin.site.register(Release)