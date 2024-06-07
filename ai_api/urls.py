from django.urls import path
from .views import assistant
from . import views

urlpatterns = [
    path("", assistant.as_view(), name="index"),
]