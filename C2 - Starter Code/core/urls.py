from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("partials/about/", views.about, name="about"),
]
