"""
URL configuration for API routes.
"""
from django.urls import path
from . import ask, search, health

urlpatterns = [
    path('ask', ask.ask, name='ask'),
    path('search', search.search, name='search'),
    path('health', health.health, name='health'),
]

