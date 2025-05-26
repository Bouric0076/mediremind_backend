from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_user),
    path("login/", views.login_user),
    path("forgot-password/", views.forgot_password),
    path("logout/", views.logout_user),
    path("whoami/", views.whoami),
]
