from django.urls import path
from .views import PetitionView, ConfirmMailView

urlpatterns = [
    path("<slug:slug>/", PetitionView.as_view(), name="petition"),
    path("confirm/<uuid:pk>", ConfirmMailView.as_view(), name="confirm")
]
