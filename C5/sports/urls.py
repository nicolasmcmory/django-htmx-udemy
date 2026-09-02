from django.urls import path
from .views import Fixtures

urlpatterns = [path("", Fixtures.as_view(), name="sports-index")]
