from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("delete-book/<int:book_id>/", views.DeleteBook.as_view(), name="delete-book"),
    path("edit-book/<int:book_id>/", views.EditBook.as_view(), name="edit-book"),
    path("search-books/", views.SearchBooks.as_view(), name="search-books"),
]
