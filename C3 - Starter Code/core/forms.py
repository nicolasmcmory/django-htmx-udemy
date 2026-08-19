from django import forms
from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["name", "genres"]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not name or name.strip() == "":
            raise forms.ValidationError("Book name cannot be empty.")
        name = name.strip()

        # Existing books check
        existing_books = self.user.get_books()
        if existing_books:
            existing_books = [book.name.lower() for book in existing_books]
            if name.lower() in existing_books:
                raise forms.ValidationError(
                    "This book already exists in your collection."
                )

        return name

    def clean_genres(self):
        genres = self.cleaned_data.get("genres")
        if not genres:
            raise forms.ValidationError("Please select a genre.")
        return genres
