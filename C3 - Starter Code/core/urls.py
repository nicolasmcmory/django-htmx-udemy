from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "delete-book/<int:book_id>/", views.DeleteBookView.as_view(), name="delete-book"
    ),
    path("edit-book/<int:book_id>/", views.EditBookView.as_view(), name="edit-book"),
]
