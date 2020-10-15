from django.urls import path

from . import views


app_name = 'url_info'
urlpatterns = [
    path('history/', views.history, name='history'),
    path('visits/', views.visit_info, name='visit_info'),
]