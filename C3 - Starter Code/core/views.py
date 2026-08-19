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
        "form": BookForm(user=user),
    }
    # Htmx check
    is_htmx = request.headers.get("HX-Request") == "true"

    # If post request then process as post
    if request.method == "POST":
        form = BookForm(request.POST, user=user)
        if form.is_valid():
            name = form.cleaned_data["name"]
            genres = form.cleaned_data["genres"]

            # If all is valid, save the book and add it to the user's collection
            book = form.save()
            user.add_book(book)

            # Render as htmx fragment if htmx is present
            if is_htmx:
                success_message = f"Book '{book.name}' added successfully!"
                return render(
                    request,
                    "index.html#book_row_empty",
                    {"book": book, "success": success_message},
                )

        # If errors pass current form in context
        else:
            context["form"] = form
            error_message = "Please correct the errors above."
            context["error"] = error_message

            # If htmx is present, render the form fragment with errors
            if is_htmx:
                return render(
                    request,
                    "index.html#book_form",
                    {"form": form, "error": error_message, "form_oob": True},
                )
            # If htmx is not present, render the full page with errors
            else:
                return render(request, "index.html", context)

    return render(request, "index.html", context)
