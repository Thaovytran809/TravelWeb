# travel/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recommend/', views.ai_recommend, name='ai_recommend'),
    path('travel-recommend/', views.travel_recommend, name='travel_recommend'),
]
