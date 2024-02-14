from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
import json
from django.http import JsonResponse

from .models import User, Post, Follow, Like


def remove_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    like = Like.objects.filter(user=user, post=post)
    like.delete()
    return JsonResponse({"message": "like removed"})


def add_like(request, post_id):
    post = Post.objects.get(pk=post_id)
    user = User.objects.get(pk=request.user.id)
    newLike = Like(user=user, post=post)
    newLike.save()
    return JsonResponse({"message": "Liked_added!"})


def index(request):
    allPosts = Post.objects.all().order_by("id").reverse()

    # count of likes
    posts = (Post.objects.all().order_by("id").reverse()).annotate(
        likes_count=Count("post_like")
    )
    # pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    post_page = paginator.get_page(page_number)

    allLikes = Like.objects.all()
    whoYouLiked = []
    try:
        for like in allLikes:
            if like.user.id == request.user.id:
                whoYouLiked.append(like.post.id)
    except:
        whoYouLiked = []

    return render(
        request,
        "network/index.html",
        {
            "allPosts": allPosts,
            "post_page": post_page,
            "whoYouLiked": whoYouLiked,
            "posts": posts,
        },
    )


def edit(request, post_id):
    if request.method == "POST":
        data = json.loads(request.body)
        edit_post = Post.objects.get(pk=post_id)
        edit_post_content = data["content"]
        edit_post.content = edit_post_content
        edit_post.save()
        return JsonResponse(
            {"message": "Successfully edited!", "data": edit_post_content}
        )


def newPost(request):
    if request.method == "POST":
        content = request.POST["content"]
        user = User.objects.get(pk=request.user.id)
        post = Post(content=content, user=user)
        post.save()
        return HttpResponseRedirect(reverse("index"))


def profile(request, user_id):
    user = User.objects.get(pk=user_id)
    allPosts = Post.objects.filter(user=user).order_by("id").reverse()

    following = Follow.objects.filter(user=user)
    followers = Follow.objects.filter(user_follower=user)

    try:
        checkFollow = followers.filter(user=User.objects.get(pk=request.user.id))
        if len(checkFollow) != 0:
            isFollowing = True
        else:
            isFollowing = False
    except:
        isFollowing = False

    allLikes = Like.objects.all().filter(user=user)
    whoYouLiked = []
    try:
        for like in allLikes:
            if like.user.id == request.user.id:
                whoYouLiked.append(like.post.id)
    except:
        whoYouLiked = []

    posts = (Post.objects.filter(user=user).order_by("id").reverse()).annotate(
        likes_count=Count("post_like")
    )

    # pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    post_page = paginator.get_page(page_number)

    return render(
        request,
        "network/profile.html",
        {
            "allPosts": allPosts,
            "post_page": post_page,
            "username": user.username,
            "following": following,
            "followers": followers,
            "isFollowing": isFollowing,
            "posts": posts,
            "user_profile": user,
            "whoYouLiked": whoYouLiked,
        },
    )


def following(request):
    currentUser = User.objects.get(pk=request.user.id)
    followingPeople = Follow.objects.filter(user=currentUser)
    allPosts = Post.objects.all().order_by("id").reverse()
    # followingPosts = []
    followingPosts = Post.objects.none()

    # for post in allPosts:
    #     for person in followingPeople:
    #         if person.user_follower == post.user:
    #             followingPosts.append(post)
    for person in followingPeople:
        followingPosts = followingPosts | Post.objects.filter(user=person.user_follower).order_by("id").reverse()

    # get the posts that the current user has liked
    allLikes = Like.objects.filter(user=currentUser)
    whoYouLiked = []
    try:
        for like in allLikes:
            if like.user.id == request.user.id:
                whoYouLiked.append(like.post.id)
    except:
        whoYouLiked = []

    # annotate the followingPosts queryset with the likes_count field
    posts = followingPosts.annotate(
        likes_count=Count("post_like")
    )

    # pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    post_page = paginator.get_page(page_number)

    return render(
        request,
        "network/following.html",
        {
            "post_page": post_page,
            "whoYouLiked": whoYouLiked,
            "posts": posts,
        },
    )


def follow(request):
    userfollow = request.POST["userfollow"]
    current_user = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userfollow)
    f = Follow(user=current_user, user_follower=userfollowData)
    f.save()
    user_id = userfollowData.id
    return HttpResponseRedirect(reverse(profile, kwargs={"user_id": user_id}))


def unfollow(request):
    userfollow = request.POST["userfollow"]
    current_user = User.objects.get(pk=request.user.id)
    userfollowData = User.objects.get(username=userfollow)
    f = Follow.objects.get(user=current_user, user_follower=userfollowData)
    f.delete()
    user_id = userfollowData.id
    return HttpResponseRedirect(reverse(profile, kwargs={"user_id": user_id}))


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
            return render(
                request,
                "network/login.html",
                {"message": "Invalid username and/or password."},
            )
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(
                request, "network/register.html", {"message": "Passwords must match."}
            )

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(
                request, "network/register.html", {"message": "Username already taken."}
            )
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")
