from django.shortcuts import render
from django.views import View
from .models import Fixture
from django.http import HttpResponse
import time


class Fixtures(View):

    # Handle GET requests to display the fixtures
    def get(self, request):
        fixtures = Fixture.objects.all()
        context = {"fixtures": fixtures}

        # Check if the request is an HTMX request and render the appropriate template
        if request.htmx:
            time.sleep(5)  # Simulate a delay for demonstration purposes
            return render(request, "sports/sports_index.html#fixtures_block", context)

        return render(request, "sports/sports_index.html", context)
