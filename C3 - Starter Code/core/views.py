from django.shortcuts import render, redirect
from .services import UserService, BookService
from .forms import BookForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages


@login_required
def index(request):
    user = UserService(request.user)
    books = user.get_books()
    context = {
        "books": books,
        "form": BookForm(),
    }

    # Htmx check
    is_htmx = request.headers.get("HX-Request") == "true"

    if request.method == "POST":
        form = BookForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            genres = form.cleaned_data["genres"]
            existing_books = user.get_books()

            # Check if the book already exists in the user's collection
            if existing_books:
                existing_books = [book.name.lower() for book in existing_books]
                if name.lower() in existing_books:
                    messages.error(
                        request,
                        f'Book "{name}" already exists!',
                        extra_tags="book-error",
                    )
                    return render(request, "index.html", context)

            # If all is valid, save the book and add it to the user's collection
            book = form.save()
            user.add_book(book)
            messages.success(
                request,
                f'Book "{book.name}" has been added successfully!',
                extra_tags="book-success",
            )

            # Render as htmx fragment if htmx is present
            if is_htmx:
                return render(
                    request, "partials/misc_partials.html#book_row", {"book": book}
                )

        # If errors pass current form in context
        else:
            context["form"] = form

    return render(request, "index.html", context)
