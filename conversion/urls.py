from django.urls import path

from . import views


app_name = "conversion"
urlpatterns = [
    path('lts/', views.long_2_short, name='long_2_short'),
    path('<slug:short_key>/', views.short_2_long, name="short_to_long"),
]