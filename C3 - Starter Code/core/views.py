# Utility modules
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.http import QueryDict
from django.shortcuts import get_object_or_404

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
    }
    # Htmx check
    is_htmx = request.headers.get("HX-Request") == "true"

    # If post request then process as post
    if request.method == "POST":
        form = BookForm(request.POST, user=user)
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
                    "index.html#book_form_add",
                    {"form": form, "error": error_message, "is_htmx": is_htmx},
                    status=422,
                )
            # If htmx is not present, render the full page with errors
            else:
                return render(request, "index.html", context)

    return render(request, "index.html", context)


# Delete book by method 1: Function-based view
def delete_book(request, book_id):
    book = BookService.get_by_id(book_id)
    book_name = book.name  # Store the book name before deletion
    book.delete()


# Delete book by method 2: Class-based view
class DeleteBookView(LoginRequiredMixin, View):
    def delete(self, request, book_id):
        user = UserService(request.user)
        books = user.get_books()
        book = BookService.get_by_id(book_id)
        book_name = book.name
        context = {
            "book": book,
        }

        # Htmx check
        is_htmx = request.headers.get("HX-Request") == "true"

        # TODO: Validate that the book belongs to the user before deletion
        user.remove_book(book)  # Remove the book from the user's collection
        books = user.get_books()
        # TODO: Include a success message in the context for htmx response
        success_message = f"Book '{book_name}' deleted successfully!"
        context["success"] = success_message
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

# TODO: verify put to post request instead
class EditBookView(LoginRequiredMixin, View):
    def get(self, request, book_id):
        user = UserService(request.user)
        book = get_object_or_404(user.get_books(), pk=book_id)
        form = BookForm(instance=book, user=user)
        context = {
            "form": form,
            "book": book,
        }
        return render(request, "index.html#book_form_edit", context)

    def post(self, request, book_id):
        user = UserService(request.user)
        book = get_object_or_404(user.get_books(), pk=book_id)
        form = BookForm(request.POST, instance=book, user=user)

        # Htmx check
        is_htmx = request.headers.get("HX-Request") == "true"

        if form.is_valid():

            book = form.save()
            success_message = f"Book '{book.name}' updated successfully!"

            # Render as htmx fragment if htmx is present and reset form
            if is_htmx:
                return render(
                    request,
                    "index.html#book_item",
                    {"book": book, "success":success_message},
                )

            else:
                return redirect("index")

        # If errors, pass current form in context
        else:
            error_message = "Please correct the errors above."

            # If htmx is present, render the form fragment with errors
            if is_htmx:
                return render(
                    request,
                    "index.html#book_form_edit",
                    {
                        "book": book,
                        "form": form,
                        "error": error_message,
                        "is_htmx": is_htmx,
                    },
                    status=422,
                )
            # If htmx is not present, render the full page with errors
            
        return render(
            request, 
            "index.html", 
            {"form": form, "error": error_message, "books": user.get_books()}
        )
