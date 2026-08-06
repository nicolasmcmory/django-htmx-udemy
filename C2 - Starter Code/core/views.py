from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
def index(request):
    if request.method == "POST" and "Hx-Request" in request.headers:
        response = {"product": request.POST.get("product"), "id": 7}
        return render(request, "partials/partials.html#products", response)

    return render(request, "index.html", {})


def about(request):
    context = {}
    if "Hx-Request" in request.headers:
        return render(request, "partials/partials.html#about", context)

    return HttpResponse("This is the about page. It is not a partial request.")


def products(request):
    return render(request, "partials/partials.html#products", {})
