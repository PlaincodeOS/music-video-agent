"""URL configuration for Break Records PoC."""

from django.urls import include, path

urlpatterns = [
    path("api/", include("agent.urls")),
]
