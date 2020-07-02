from django.urls import path
from .views import stations, election

urlpatterns = [
    path('stations', stations),
    path('election', election.run)
]
