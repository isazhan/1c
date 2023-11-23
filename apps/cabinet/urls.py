from django.urls import path
from . import views

urlpatterns = [
    path('login_user', views.login_user, name='login_user'),
    path('logout_user', views.logout_user, name='logout_user'),
    path('', views.cabinet, name='cabinet'),
    path('instances', views.instances, name='instances'),
    path('create_instance', views.create_instance, name='create_instance'),
]