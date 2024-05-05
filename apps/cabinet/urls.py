from django.urls import path
from . import views

urlpatterns = [
    path('sign_up', views.sign_up, name='sign_up'),
    path('login_user', views.login_user, name='login_user'),
    path('logout_user', views.logout_user, name='logout_user'),
    path('', views.cabinet, name='cabinet'),
    path('instances', views.instances, name='instances'),
    path('create_instance', views.create_instance, name='create_instance'),
    path('create_driver', views.create_driver, name='create_driver'),
    path('get_qr', views.get_qr, name='get_qr'),
    path('check_auth', views.check_auth, name='check_auth'),
    path('instances/<int:inst_number>/', views.instance, name='instance'),
    path('one_message', views.one_message, name='one_message'),
    path('few_messages', views.few_messages, name='few_messages'),
    path('message_order', views.message_order, name='message_order'),
    path('auth_instance', views.auth_instance, name='auth_instance'),
]