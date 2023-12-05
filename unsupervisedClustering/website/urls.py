from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('upload_model/', views.upload_model, name='upload_model'),
    path('test_model/', views.test_model, name='test_model'),
]