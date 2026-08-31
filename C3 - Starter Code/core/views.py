# Utility modules
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import QueryDict
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.db.models import Q

# Local modules
from .services import UserService, BookService
from .forms import BookForm


@login_required
def index(request):
    user = UserService(request.user)
    books = user.get_books()
    context = {
        "books": books,
        "form": BookForm(user=user),
        "form_id": "book-form-add",
        "form_action": reverse("index"),
        "form_target": "#book-list",
        "form_swap": "afterbegin",
    }
    # Htmx check
    is_htmx = request.headers.get("HX-Request") == "true"

    # If post request then process as post
    if request.method == "POST":
        form = BookForm(request.POST, request.FILES, user=user)
        if form.is_valid():
            name = form.cleaned_data["name"]
            genres = form.cleaned_data["genres"]

            # If all is valid, save the book and add it to the user's collection and update the context for full page render and htmx fragment render
            book = form.save()
            user.add_book(book)
            success_message = f"Book '{book.name}' added successfully!"
            context["success"] = success_message
            context["form"] = BookForm(user=user)
            context["books"] = user.get_books()

            # Render as htmx fragment if htmx is present and reset form
            if is_htmx:
                return render(
                    request,
                    "index.html#book_table",
                    {
                        "book": book,
                        "is_htmx": is_htmx,
                        "success": success_message,
                        "books": context["books"],
                    },
                )

            else:
                return render(request, "index.html", context)

        # If errors, pass current form in context
        else:
            context["form"] = form
            error_message = "Please correct the errors above."
            context["error"] = error_message

            # If htmx is present, render the form fragment with errors
            if is_htmx:
                return render(
                    request,
                    "index.html#book_form",
                    {
                        "form": form,
                        "error": error_message,
                        "is_htmx": is_htmx,
                        "form_id": "book-form-add",
                        "form_action": reverse("index"),
                        "form_target": "#book-list",
                        "form_swap": "afterbegin",
                    },
                    status=422,
                )
            # If htmx is not present, render the full page with errors
            else:
                return render(request, "index.html", context)

    return render(request, "index.html", context)


# Delete book by method 2: Class-based view
class DeleteBook(LoginRequiredMixin, View):
    def delete(self, request, book_id):
        user = UserService(request.user)
        books = user.get_books()
        book = get_object_or_404(books, pk=book_id)
        book_name = book.name
        context = {
            "book": book,
        }

        # Htmx check
        is_htmx = request.headers.get("HX-Request") == "true"

        user.remove_book(book)  # Remove the book from the user's collection

        # Only delete the book (and its image via the post_delete signal)
        # if no other user still tracks it
        if not book.users.exists():
            book.delete()

        books = user.get_books()
        if is_htmx:
            # Return the empty-state OOB fragment so it becomes visible once the last book is removed
            return render(
                request,
                "index.html#book_table_empty",
                {"books": books},
            )
        # Full page redirect if not htmx
        else:
            return redirect("index")


class EditBook(LoginRequiredMixin, View):

    def get(self, request, book_id):
        user = UserService(request.user)
        book = get_object_or_404(user.get_books(), pk=book_id)
        form = BookForm(instance=book, user=user)

        # Check if the request is an htmx request
        if request.htmx:
            return render(
                request,
                "index.html#book_form",
                {
                    "form": form,
                    "book": book,
                    "is_htmx": True,
                    "is_edit": True,
                    "form_id": "book-form-edit",
                    "form_action": reverse("edit-book", args=[book.pk]),
                    "form_target": f"#book-{book.pk}",
                    "form_swap": "outerHTML",
                },
            )
        return redirect("index")

    def post(self, request, book_id):
        user = UserService(request.user)
        book = get_object_or_404(user.get_books(), pk=book_id)
        form = BookForm(request.POST, instance=book, user=user)

        if form.is_valid():

            book = form.save()
            success_message = f"Book '{book.name}' updated successfully!"

            # Render as htmx fragment if htmx is present and reset form
            if request.htmx:
                return render(
                    request,
                    "index.html#book_item",
                    {"book": book, "success": success_message},
                )

            else:
                return redirect("index")

        # If errors, pass current form in context
        else:
            error_message = "Please correct the errors above."

            # If htmx is present, render the form fragment with errors
            if request.htmx:
                return render(
                    request,
                    "index.html#book_form",
                    {
                        "book": book,
                        "form": form,
                        "error": error_message,
                        "is_htmx": True,
                        "is_edit": True,
                        "form_id": "book-form-edit",
                        "form_action": reverse("edit-book", args=[book.pk]),
                        "form_target": f"#book-{book.pk}",
                        "form_swap": "outerHTML",
                    },
                    status=422,
                )
            # If htmx is not present, render the full page with errors

        return redirect("index")


class SearchBooks(LoginRequiredMixin, View):
    def get(self, request):
        user = UserService(request.user)
        books = user.get_books()
        query = request.GET.get("search", "")
        # Get the first matching book for both name and genre search
        books = books.filter(Q(name__icontains=query) | Q(genres__icontains=query))
        print(f"Search query: {query}")  # Debugging line
        return render(request, "index.html#search_table", {"books": books})
