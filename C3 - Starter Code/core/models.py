from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class User(AbstractUser):
    books = models.ManyToManyField("Book", related_name="users")


class Book(models.Model):
    class GenreChoices(models.TextChoices):
        FICTION = "fiction"
        NON_FICTION = "non-fiction"
        MYSTERY = "mystery"
        ROMANCE = "romance"
        FANTASY = "fantasy"

    name = models.CharField(max_length=172)
    genres = models.CharField(max_length=20, choices=GenreChoices.choices)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created"]  # Returns the most recently created books first

    def __str__(self):
        return self.name
