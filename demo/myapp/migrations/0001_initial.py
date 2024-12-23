# Generated by Django 5.0.6 on 2024-08-06 21:37

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Release",
            fields=[
                ("title", models.CharField(max_length=255)),
                ("cover_image", models.URLField()),
                (
                    "release_id",
                    models.CharField(max_length=255, primary_key=True, serialize=False),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Collection",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("collection_name", models.CharField(max_length=255)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("releases", models.ManyToManyField(to="myapp.release")),
            ],
        ),
    ]
