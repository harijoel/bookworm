from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("book/<str:isbn>", views.book, name="book"),
    path("user/<str:username>", views.userProfile, name="user"),
    path("register", views.register, name="register"),
    path("likeReview", views.likeReview, name="likeReview"),
    path("search", views.search, name="search"),
    path("lucky", views.lucky, name="lucky")
]