"""URL configuration for Break Records PoC."""

from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda request: redirect("/api")),
    path("api/", include("agent.urls")),
]
