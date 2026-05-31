from django.urls import path

from agent.views import generate_video, index

urlpatterns = [
    path("", index, name="index"),
    path("generate/", generate_video, name="generate_video"),
]
