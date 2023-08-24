from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from .models import Book, Review, User
from django.db.models import Q
from django.db.models import Avg
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.contrib.auth.decorators import login_required
import requests
from random import choice

# Create your views here.
def index(request):
    bumped = []
    seen = set()
    latest_reviews = Review.objects.all().order_by("-id")
    for review in latest_reviews:
        if review.book.id not in seen:
            bumped.append(review.book)
            seen.add(review.book.id)
            
    #books = Book.objects.all()
    return render(request, "bookcatalog/index.html", {"results": bumped})

def search(request):
    if request.method == "GET":
        query = request.GET["q"]
        results = Book.objects.filter(Q(title__icontains=query) | Q(isbn__icontains=query) | Q(author__icontains=query))
        numres = len(results)
        return render(request, "bookcatalog/search.html", {"results": results, "numres": numres})
    
def lucky(request):
    pks = Book.objects.values_list('pk', flat=True)
    random_pk = choice(pks)
    random_obj = Book.objects.get(pk=random_pk)
    return HttpResponseRedirect(reverse("book", args=(random_obj.isbn, )))

# Fix bug here ##########################
def likeReview(request):
    # Liking a post mut be via POST
    if request.method == "POST":
        # Check if user already liked the post
        user = request.user
        review_id = request.POST["review_id"]
        review = Review.objects.get(pk=review_id)
        if user not in review.likers.all():
            review.likers.add(user)
        else: # Unlike if already liked
            review.likers.remove(user)
        return HttpResponseRedirect(reverse("book", args=(review.book.isbn, )))
    return render(request, "bookcatalog/error.html", {"message": "Can't close an auction through POST method"})

def book(request, isbn):
    # Fetch book
    try:
        book = Book.objects.get(isbn=isbn)
    except ObjectDoesNotExist:
        return render(request, "bookcatalog/error.html")
    user = request.user
    
    # Fetch user's  review (if any)
    try:
        userrev = user.reviews.get(book=book)
    except:
        userrev = None
        
    
    if request.method == "POST":
        # Collect form data (rating & comment)
        try:
            rating = int(request.POST["rating"])
        except:
            return render(request, "bookcatalog/error.html", {"message": "invalid rating"})
        comment = request.POST["comment"]
        if len(comment) < 3 or len(comment) > 250:
            return render(request, "bookcatalog/error.html", {"message": "invalid comment length"})
        
        # Delete previous review (if any)
        if userrev:
            userrev.delete()
        
        # Insert review
        review = Review(user=user, book=book, comment=comment, rating=rating)
        review.save()
        return HttpResponseRedirect(reverse("book", args=(book.isbn, )))
    
    # Fetch reviews form database for display
    reviews = book.reviews.all()
    
    # Get bookworm stats
    rating_cnt = book.reviews.all().count()
    rating_avg = book.reviews.aggregate(average=Avg('rating'))["average"]
    bwstat = {"count": rating_cnt, "avg": rating_avg}
    
    # GOODREADS REVIEW
    key = "5E0UYC3NMdKBccVajqIA"
    res = requests.get(f"https://openlibrary.org/works/{isbn}/ratings.json")
    # if res.status_code != 200:
    #     raise Exception("ERROR: API request unsuccessful.")
    data = res.json()
    goodstat = data
    
    rrange = [5, 4, 3, 2, 1]
    return render(request, "bookcatalog/book.html", {
        "book": book, 
        "reviews": reviews, 
        "userrev": userrev, 
        "rrange": rrange,
        "bwstat": bwstat,
        "goodstat": goodstat})

def userProfile(request, username):
    # User exists
    try:
        user = User.objects.get(username=username)
    except ObjectDoesNotExist:
        message = "User not found"
        return render(request, "bookcatalog/error.html", {"message": message})
    
    # Fetch books where user commented
    userReviews = user.reviews.all()
    return render(request, "bookcatalog/user.html", {"userReviews": userReviews, "username": username})
    
def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            message = "Incorrect username or password"
            return render(request, "bookcatalog/login.html", {"message": message, "username": username, "password": password})
    else:
        return render(request, "bookcatalog/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["username"]
        confirmation = request.POST["confirmation"]
        terms = True #request.POST["terms"]
        failed = False
        # Username was submitted
        if not username:
            message = "You must provide a username"
            failed = True
        # Only letters and numbers
        if not username.isalnum():
            message = "Username must only contain letters or numbers"
            failed = True
        # Username length fits
        if not (3 <= len(username) <= 12):
            message = "Username must be between 3 and 12 characters in length"
            failed = True
        # Password was submitted
        if not password:
            message = "You must provide a password"
            failed = True
        # Ensure password matches confirmation
        if password != confirmation:
            message = "Passwords do not match"
            failed = True
        # Password length fits
        if not (3 <= len(password) <= 12) or not (3 <= len(confirmation) <= 12):
            message = "Password must be between 3 and 12 characters in length"
            failed = True
        
        #Terms were accepted
        if not terms:
            message = "You must accept the terms"
            failed = True
        if failed:
            return render(request, "bookcatalog/register.html", {"message": message})
        # Attempt to create new user / #Username is not taken
        try:
            user = User.objects.create_user(username=username, password=password)
            user.save()
        except IntegrityError:
            message = "Username already taken."
            failed = True
        if failed:
            return render(request, "bookcatalog/register.html", {"message": message})
        
        # Login if passed all filters
        login(request, user)
        # Redirect to login
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "bookcatalog/register.html")
