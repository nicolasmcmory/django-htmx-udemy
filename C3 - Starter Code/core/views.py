from django.shortcuts import render
from .services import UserService
from .forms import BookForm
from django.contrib.auth.decorators import login_required


# Return all books for given user
@login_required
def index(request):
    user = UserService(request.user)
    books = user.get_books()
    context = {"books": books, "form": BookForm()}
    return render(request, "index.html", context)
