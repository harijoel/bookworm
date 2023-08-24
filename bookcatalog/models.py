from django.contrib.auth.models import AbstractUser
from django.db import models


#Create your models here.
class User(AbstractUser):
    following = models.ManyToManyField('self', blank=True, symmetrical=False, related_name="followers")
    
class Book(models.Model):
    isbn = models.CharField(max_length=13)
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    year = models.CharField(max_length=16)
    
    def __str__(self):
        return f"{self.title} by {self.author}"
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    comment = models.CharField(max_length=250)
    rating = models.PositiveSmallIntegerField()
    time = models.DateTimeField(auto_now_add=True)
    likers = models.ManyToManyField(User, blank=True, related_name="likes")
    
    def serialize(self):
        return {
            "id": self.id,
            "user": self.user.username,
            "time": self.time.strftime("%b %d %Y, %I:%M %p"),
            "comment": self.comment,
            "numlikes": self.likers.all().count()
        }
    
    def __str__(self):
        return f"Post #{self.id} by {self.user} on {self.time.strftime('%d %b %Y %H:%M:%S')}"
