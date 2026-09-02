from django.shortcuts import render
from django.views import View
from .models import Fixture
from django.http import HttpResponse


class Fixtures(View):
    def get(self, request):
        fixtures = Fixture.objects.all()
        context = {"fixtures": fixtures}
        return render(request, "sports/sports_index.html", context)
