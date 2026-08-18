from django import forms
from .models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["name", "genres"]

    def clean_name(self):
        name = self.cleaned_data.get("name")
        if not name or name.strip() == "":
            raise forms.ValidationError("Book name cannot be empty.")
        return name.strip()

    def clean_genres(self):
        genres = self.cleaned_data.get("genres")
        if not genres:
            raise forms.ValidationError("Please select a genre.")
        return genres
