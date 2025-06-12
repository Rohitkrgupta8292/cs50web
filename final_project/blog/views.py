# from datetime import datetime
# from django.contrib.admin.models import LogEntry
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.utils.crypto import get_random_string
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from rest_framework.parsers import JSONParser
from django.urls import reverse
from PIL import Image
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from django.utils.text import slugify
import requests
import urllib.parse
# from django.utils import timezone
from django.utils.timezone import now, timedelta
from django.db.models import Q
from .models import User, PasswordResetToken, Post, Comment, Like, SocialMediaLink, Follow, Category, Tag, Notification, SearchQuery, Activity
import json
import re
# import html
# import random
# Get the current year
current_year = now().year

# @login_required
# @csrf_exempt
# def upload_image(request):
    # if request.method == 'POST' and request.FILES.get('file'):
    #     image = request.FILES.get('file')
    #     # Save the image to the default storage
    #     file_path = default_storage.save(f"tinymce_images/{image.name}", ContentFile(image.read()))
    #     return JsonResponse({'location': default_storage.url(file_path)})
    # return JsonResponse({'error': 'image upload failed'}, status=400)

# signin provider
def github_login(request):
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_CALLBACK_URL}&scope=user"
    return redirect(github_auth_url)


def github_callback(request):
    code = request.GET.get("code")
    token_url = "https://github.com/login/oauth/access_token"
    data = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "client_secret": settings.GITHUB_CLIENT_SECRET,
        "code": code,
    }
    headers = {"Accept": "application/json"}
    response = requests.post(token_url, json=data, headers=headers)
    response_data = response.json()
    access_token = response_data.get("access_token")

    # Use the access token to get user information
    try:
        user_info_url = "https://api.github.com/user"
        user_response = requests.get(
            user_info_url, headers={"Authorization": f"token {access_token}"}
        )
        user_data = user_response.json()
        # Create a new user or get the existing user
        user, created = User.objects.get_or_create(
            username=user_data["login"], defaults={"email": user_data["email"]}
        )
        if created:
            user.auth_method = "github"
            user.save()
        if user.auth_method != "github":
            messages.error(request, "You didn't create your account with github")
            return redirect("login")
        login(request, user)
        return redirect("/")
    except ValueError:
        messages.error(request, "Invalid token.")
        return redirect("login")


# google signin
def google_login(request):
    # Redirect to Google's OAuth 2.0 server
    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={settings.GOOGLE_CALLBACK_URL}&response_type=code&scope=openid email profile"
    return redirect(google_auth_url)


def google_callback(request):
    code = request.GET.get("code")
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_CALLBACK_URL,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    response_data = response.json()

    if "error" in response_data:
        messages.error(request, f"Error during Google login: {response_data['error']}")
        return redirect("login")
    access_token = response_data.get("access_token")

    # Verify the token and get user info
    try:
        idinfo = id_token.verify_oauth2_token(
            access_token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
        user_email = idinfo["email"]
        user = User.objects.get(email=user_email)
        # use get -r create to find or create the user
        user, created = User.objects.get_or_create(email=user_email)
        if created:
            user.auth_method = "google"
            user.username = idinfo.get("name", user_email.split("@")[0])
            user.save()
            messages.success(request, "Account created successfully with Google.")
        else:
            if user.auth_method != "google":
                messages.error(request, "You didn't create your account with google.")
                return redirect("login")
        login(request, user)
        return redirect("/")  # Redirect to a success page or home page
    except ValueError:
        messages.error(request, "Invalid token.")
        return redirect("login")
    except Exception:
        messages.error(request, "An error occurred during login.")
        return redirect("login")


# unautheticated user view
def unauthenticated_user(view_func):
    def wrapper_func(request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(
                reverse("home")
            )  # Redirect to home if user is authenticated
        else:
            return view_func(request, *args, **kwargs)

    return wrapper_func

def home(request):
    # Fetch all posts ordered by creation date (assuming you have a 'created_at' field)
    # current_tab = request.GET.get('tab', 'LatestPosts')
    posts = Post.objects.all().order_by('-created_at')[:6]  # Fetch only 6 posts
    total_posts = Post.objects.count() # get total number of posts
    if request.user.is_authenticated:
        user = request.user
        # PASS boolean value to make sidebar home button active 
        sidebar_active_home = True
        # get all latest posts
        latest_posts = Post.objects.all().order_by('-created_at')
        # get all posts of the following user, followed by requested user
        following_posts = Post.objects.filter(author__followers__follower=user).order_by('-created_at')
        # get all posts which is liked by request user.
        liked_posts = Post.objects.filter(likes__user=user).order_by('-created_at')
        # check latest post author is followed by user or not and add in a list
        is_following_authors = []
        for post in latest_posts:
            is_following_authors.append(is_following(request, post.author.username))
        # zip latest_posts with is_following_authors
        latest_posts_with_is_following = zip(latest_posts, is_following_authors)
        # check liked post author is followed by user or not and add in a list
        is_following_liked = []
        for post in liked_posts:
            is_following_liked.append(is_following(request, post.author.username))
        # zip liked_posts with is_following_liked
        liked_posts_with_is_following = zip(liked_posts, is_following_liked)

        return render(
            request, "home_login.html", {"current_year": current_year, "sidebar_active_home": sidebar_active_home, "latest_posts": latest_posts, "following_posts": following_posts, "liked_posts": liked_posts, "latest_posts_with_is_following": latest_posts_with_is_following, "liked_posts_with_is_following": liked_posts_with_is_following}
        )  
    return render(
            request, "home.html", {"current_year": current_year, "posts": posts, "total_posts": total_posts}
        )

@login_required
def create_post(request):
    #pass existing category to template
    categories = Category.objects.all().order_by('name')
    user = request.user
    if request.method == "POST":
        title = request.POST.get('title').strip()
        if title == '':
            title = None
        else:
           # check that title of slug exist or not
            slug = slugify(title)
            post_exists = Post.objects.filter(slug=slug).exists()
            if post_exists:
                # if post exists, append a number to the slug
                i = 1
                while True:
                    new_slug = f"{slug}-{i}"
                    if not Post.objects.filter(slug=new_slug).exists():
                        slug = new_slug
                        break
                    i += 1
        content = request.POST.get('content').strip()
        content1 = re.sub(r'<.*?>', '', content).replace('&nbsp;', '').strip()
        if content1 == '':
            print('empty')
            content1 = None
        category_id = request.POST.get('category')

        if category_id != '':
            category = Category.objects.get(id=category_id)
        else:
            category = None
        tags = request.POST.get('tags').strip()
        if tags == '':
            tags = None

        if 'thumbnail' in request.FILES:
           thumbnail = request.FILES.get('thumbnail')
           try:
               img = Image.open(thumbnail)
               img.verify()
           except IOError:
               thumbnail = None
               messages.error(request, 'Please upload a valid image file')
               return redirect('create_post')
        
           
        if title is None or content1 is None or thumbnail is None:
            messages.error(request, "Please fill the required fields")
        else:
            post = Post(title=title, content=content, author=user, thumbnail=thumbnail, slug=slug)
            if category is not None:
                post.category = category
            post.save()
            if tags is not None:
                for tag in tags.split(','):
                    tag = tag.strip()
                    if tag:
                        tag_instance, created = Tag.objects.get_or_create(name=tag)
                        post.tags.add(tag_instance)
            post.save()
            #create activity for create post
            Activity.objects.create(user=user, action_type='post_create', post=post)
            for follower in request.user.followers.all():
                Notification.objects.create(user=follower.follower , notification_type='post', post=post, actor=request.user)
            messages.success(request, "Post created successfully")
            return redirect(post.get_absolute_url())
    return render(request, "create_post.html", {"categories": categories})

@login_required
def dashboard(request):
    user = request.user
    sidebar_active_dashboard = True
    posts_show = Post.objects.filter(author=user).order_by('-created_at')
    query = request.GET.get('q','')
    if query != '':
        posts = posts_show.filter(Q(title__icontains=query)).distinct()
    else:
        posts = posts_show
    # total post count
    post_count = Post.objects.filter(author=user).count()
    # total likes all user post
    post_likes_count = Like.objects.filter(post__author=user).count()
    # total comments all user post
    post_comments_count = Comment.objects.filter(post__author=user).count()
    return render(request, "dashboard.html", {"posts": posts, "post_likes_count": post_likes_count, "post_comments_count": post_comments_count, "current_year": current_year, "sidebar_active_dashboard": sidebar_active_dashboard, "post_count": post_count, "query": query})

@login_required
def update_post(request, slug):
    user = request.user
    post = get_object_or_404(Post, slug=slug, author=user)
    categories = Category.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title').strip()
        if title == '':
            title = None
        else:
            new_slug = slugify(title)
            if new_slug != post.slug:
                post_exists = Post.objects.filter(slug=new_slug).exists()
                if post_exists:
                    i = 1
                    while True:
                        new_slug = f"{slugify(title)}-{i}"
                        if not Post.objects.filter(slug=new_slug).exists():
                            break
                        i += 1
            else:
                new_slug = post.slug
        content = request.POST.get('content').strip()
        content1 = re.sub(r'<.*?>', '', content).replace('&nbsp;', '').strip()
        if content1 == '':
            print('empty')
            content1 = None
        category_id = request.POST.get('category')
        if category_id != '':
            category = Category.objects.get(id=category_id)
        else:
            category = None
        tags = request.POST.get('tags').strip()
        if tags == '':
            tags = None
        if 'thumbnail-new' in request.FILES:
            thumbnail = request.FILES.get('thumbnail-new')
            try:
                img = Image.open(thumbnail)
                img.verify()
            except IOError:
                thumbnail = None
                messages.error(request, 'Please upload a valid image file')
                return redirect('update_post', slug=slug)
        else:
            thumbnail = post.thumbnail
        if title is None or content1 is None or thumbnail is None:
            messages.error(request, "Please fill the required fields")
        else:
            post.title = title
            post.content = content
            post.thumbnail = thumbnail
            post.slug = new_slug
            if category is not None:
                post.category = category
            post.tags.clear()
            if tags is not None:
                for tag in tags.split(','):
                    tag = tag.strip()
                    if tag:
                        tag_instance, created = Tag.objects.get_or_create(name=tag)
                        post.tags.add(tag_instance)
            post.save()
            # Activity for update post
            Activity.objects.create(user=user, action_type='post_update', post=post)
            messages.success(request, "Post updated successfully")
            return redirect(post.get_absolute_url())
    return render(request, "update_post.html", {"post": post, "categories": categories})

@login_required
def delete_post(request, slug):
    user = request.user
    post = get_object_or_404(Post, slug=slug, author=user)
    if request.method == 'POST':
        post.delete()
        # Activity for delete post
        messages.success(request, "Post deleted successfully")
        return redirect('dashboard')
    return redirect('dashboard')

@login_required
@require_http_methods(['POST'])
def add_category(request):
    category_name = request.POST.get('category_name').strip()
    if  category_name == '':
        messages.error(request, "Please enter a category name")
    else:
        category, created = Category.objects.get_or_create(name=category_name)
        if created:
            messages.success(request, "Category added successfully")
        else:
            messages.info(request, "Category already exists")
    return redirect("create_post")

@login_required
@require_http_methods(['POST'])
def search(request):
    parser = JSONParser()
    data = parser.parse(request)
    query = data.get('query')
    # print('Search query:', query)
    results = []
    if query:
        words = query.split()
        q = Q()
        for word in words:
            q |= Q(title__icontains=word) | Q(category__name__icontains=word) | Q(tags__name__icontains=word)
        posts = Post.objects.filter(q).distinct()
        # posts = Post.objects.filter(Q(title__icontains=query) | Q(category__name__icontains=query) | Q(tags__name__in=query))
        users = User.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query))

        for post in posts:
            post_data = {
                'id': post.id,
                'thumbnail': post.thumbnail.url if post.thumbnail else None,
                'title': post.title[:25]  + '...' if len(post.title) > 25 else post.title,
                'content': post.content[:50] + '...' if len(post.content) > 50 else post.content,
                'url': post.get_absolute_url(),
            }
            results.append({'type': 'post', 'data': post_data})
        
        for user in users:
            user_data = {
                'id': user.id,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'url': user.get_absolute_url(),
            }
            results.append({'type': 'user', 'data': user_data})
    # print('Search results:', results)
    return JsonResponse({'results': results}, content_type='application/json')

@login_required
@require_http_methods(['GET'])
def recent_searches(request):
    user = request.user
    recent_searches = SearchQuery.objects.filter(user=user).order_by('-created_at')[:10]
    data = []
    for search in recent_searches:
        data.append({'query': search.query})
    return JsonResponse(data, safe=False)

@login_required
@require_http_methods(['POST'])
def save_search_query(request):
    try:
        user = request.user
        data = json.loads(request.body)
        query = data.get('query')
        existing_query = SearchQuery.objects.filter(user=user, query=query).exists()
        if existing_query:
            SearchQuery.objects.filter(user=user, query=query).delete()
            SearchQuery.objects.create(user=user, query=query)
            return JsonResponse({'message': 'previous Search query delete and new created'})
        else:
            SearchQuery.objects.create(user=user, query=query)
            return JsonResponse({'message': 'Search query saved successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e), 'message': 'Error saving search query'})

@login_required
def delete_search_query(request, query):
    if request.method == 'DELETE':
        try:
           query = SearchQuery.objects.get(query=query)
           query.delete()
           return JsonResponse({'success': True, 'message': 'Search query deleted successfully'})
        except SearchQuery.DoesNotExist:
           return JsonResponse({'success': False, 'error': 'Search query not found'})
        except Exception as e:
           return JsonResponse({'success': False, 'error': str(e)})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    like, created = Like.objects.get_or_create(user=user, post=post)

    if not created:
        like.delete()
        # Activity for unlike the post
        Activity.objects.create(user=user, action_type='post_unlike', post=post)
        Notification.objects.filter(user=post.author, notification_type='like', post=post, actor=user).delete()
        liked = False
    else:
        liked = True
        # Activity for like post
        Activity.objects.create(user=user, action_type='post_like', post=post)
        if user != post.author:
            Notification.objects.create(user=post.author, notification_type='like', post=post, actor=user)

    total_likes = post.likes.count()
    user_data = {
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'profile_picture_url': user.profile_picture.url if user.profile_picture else None,
    }

    return JsonResponse({'liked': liked, 'total_likes': total_likes, 'user': user_data})

def is_following(request, username):
    if request.user.is_authenticated:
        user = get_object_or_404(User, username=username)
        return Follow.objects.filter(follower=request.user, following=user).exists()
    return False

def post_detail(request, slug):
    post = get_object_or_404(Post, slug=slug) # retrieve the post using the slug 
    related_posts = Post.objects.filter(author=post.author).order_by('-created_at').exclude(id=post.id)[:3] # get the latest post of the author
    related_posts_count = related_posts.count() # get the total number of related posts
    comments = Comment.objects.filter(post=post, parent=None).order_by('-created_at') # get the comments of the post 
    is_following_user = is_following(request, post.author.username)
    post_likes = post.likes.all() # get the likes of the post
    is_following_likes = []
    for like in post_likes:
        is_following_likes.append(is_following(request, like.user.username))
    post_likes_with_is_following = zip(post_likes, is_following_likes)
    # check if the user is authenticated before querying likes   
    if request.user.is_authenticated:
        user_has_liked = Like.objects.filter(post=post, user=request.user).exists()
    else:
        user_has_liked = False
        # user_following = False

    if request.method == "POST":
        content = request.POST["content"].strip()
        parent_obj = None
        try:
            parent_id = int(request.POST["parent_id"])
        except:
            parent_id = None
        if parent_id:
            parent_obj = Comment.objects.get(id=parent_id)
            if parent_obj:
                reply_comment = Comment(post=post, author=request.user, content=content, parent=parent_obj)
                reply_comment.save()
                # Activity for post reply
                Activity.objects.create(user=request.user, action_type='post_reply', post=post, comment=reply_comment)
                if parent_obj.author == reply_comment.author:
                    if parent_obj.author != post.author:
                        Notification.objects.create(user=post.author, notification_type='reply', post=post, comment=reply_comment, actor=request.user)
                else:
                    if parent_obj.author == post.author:
                        Notification.objects.create(user=parent_obj.author, notification_type='reply1', post=post, comment=reply_comment, actor=request.user)
                    else:
                        Notification.objects.create(user=post.author, notification_type='reply', post=post, comment=reply_comment, actor=request.user)
                        Notification.objects.create(user=parent_obj.author, notification_type='reply1', post=post, comment=reply_comment, actor=request.user)

                messages.success(request, "Reply posted successfully")
                return redirect(post.get_absolute_url())
        comment = Comment(post=post, author=request.user, content=content)
        comment.save()
        # Activity for post comment
        Activity.objects.create(user=request.user, action_type='post_comment', post=post, comment=comment)
        if post.author != comment.author:
            Notification.objects.create(user=post.author, notification_type='comment', post=post, comment=comment, actor=request.user)
        messages.success(request, "Comment posted successfully")
        return redirect(post.get_absolute_url())
    return render(request, "post_detail.html", {"post": post, "current_year": current_year, "related_posts": related_posts, "related_posts_count": related_posts_count, "comments": comments, "user_has_liked": user_has_liked,"post_likes_with_is_following": post_likes_with_is_following, "is_following_user": is_following_user})

@login_required
def category_posts(request, category):
    # filter the post using category name
    # is_category = True
    category_name = get_object_or_404(Category, name=category)
    recent_posts = Post.objects.filter(category=category_name).order_by('-created_at')
    oldest_posts = Post.objects.filter(category=category_name).order_by('created_at')
    total_posts = Post.objects.filter(category=category_name).count()
    return render(request, "category.html", {"recent_posts": recent_posts, "oldest_posts": oldest_posts, "current_year":current_year, "total_posts":total_posts, "category":category_name})

@login_required
def tag_posts(request, tag):
    # filter the post using tag name
    # is_tag = True
    tag_name = get_object_or_404(Tag, name=tag)
    recent_posts = Post.objects.filter(tags=tag_name).order_by('-created_at')
    oldest_posts = Post.objects.filter(tags=tag_name).order_by('created_at')
    total_posts = Post.objects.filter(tags=tag_name).count()
    return render(request, "tag.html", {"recent_posts": recent_posts, "oldest_posts":oldest_posts, "total_posts":total_posts, "current_year":current_year, "tag":tag_name})

@login_required
def marks_notifications_read(request):
    notifications = Notification.objects.filter(user=request.user, read=False)
    for notification in notifications:
        notification.read = True
        notification.save()
    return redirect('notifications')

@login_required
def notifications(request):
    # showing all notitfication for last 24 hours
    sidebar_active_notifications = True
    unread_count = Notification.objects.filter(user=request.user, read=False).count()
    last_24_hours = now() - timedelta(hours=24)
    all_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    recent_notifications = all_notifications.filter(created_at__gte=last_24_hours)
    return render(request, "notifications.html", { "recent_notifications": recent_notifications, "unread_count":unread_count, "current_year":current_year, "sidebar_active_notifications":sidebar_active_notifications})

@login_required
def user_activity(request):
    user = request.user
    sidebar_active_activity = True
    activity = False
    #get the log entries for the current user in the last 24 hours
    last_24_hours = now() - timedelta(hours=24)
    user_activities = Activity.objects.filter(user=user, timestamp__gte=last_24_hours).order_by('-timestamp')
    return render(request, "user_activity.html", {"user_activities": user_activities, "sidebar_active_activity": sidebar_active_activity, "activity": activity})

@login_required(login_url='login')
def user_profile(request, username):
    # requested_user = request.user
    user = get_object_or_404(User, username=username) # retrieve the user using the username
    # PASS boolean value to make sidebar home button active 
    sidebar_active_user =  request.user == user
    followings = Follow.objects.filter(follower=user).order_by('-created_at')[:10] # get the followings of the user
    followers = Follow.objects.filter(following=user).order_by('-created_at')[:10] # get the followers of the user
    # total count or followers and following without limitation of 10
    total_followers = Follow.objects.filter(following=user).count()
    total_followings = Follow.objects.filter(follower=user).count()
    # Check if the current user is following or being followed by the requested user
    is_following_users = []
    for following in followings:
        is_following_users.append(is_following(request, following.following.username))
    # zip followings with is_following_users
    followings_with_is_following = zip(followings, is_following_users)
    is_follower_users = []
    for follower in followers:
        is_follower_users.append(is_following(request, follower.follower.username))
    # zip followings with is_following_users
    followers_with_is_following = zip(followers, is_follower_users)
    # user_following = followers.filter(follower=request.user, following=user).exists()
    # user_follower = followings.filter(following=request.user).exists()
    is_following_user = is_following(request, user.username)
    posts = Post.objects.filter(author=user).order_by('-created_at')[:6] # get the posts of the user
    # total count or posts without limitation of 10
    total_posts = Post.objects.filter(author=user).count()
    social_media_links = SocialMediaLink.objects.filter(user=user) # get the social media links of the user

    return render(request, "user_profile.html", {"user": user, "current_year": current_year, "posts": posts, "social_media_links": social_media_links, "followers": followers,"followings": followings, "is_following_user": is_following_user, "followings_with_is_following": followings_with_is_following, "followers_with_is_following": followers_with_is_following, "sidebar_active_user": sidebar_active_user, "total_followers": total_followers, "total_followings": total_followings, "total_posts": total_posts})

@login_required
def user_settings(request):
    user = request.user
    current_tab = request.GET.get('tab', 'GeneralSettings')
    sidebar_active_settings = True
    social_media_links = SocialMediaLink.objects.filter(user=user)
    #create a dictionary to map social media types to thier links
    social_media_links_dict = {}
    for link in social_media_links:
        social_media_links_dict[link.link_type] = link.link_url
    
    return render(request, 'settings.html', {'user':user, "sidebar_active_settings": sidebar_active_settings, "social_media_dict": social_media_links_dict, "current_tab":current_tab})

def is_valid_link(link):
    try:
        result = urllib.parse.urlparse(link)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@login_required
@require_http_methods(['POST'])
def save_social_links(request):
    user = request.user
    current_tab = request.GET.get('tab')
    Social_media_links = SocialMediaLink.objects.filter(user=user)
    if 'twitter' in request.POST:
        if request.POST['twitter'].strip() != '':
            twitter_exist = Social_media_links.filter(link_type='twitter').exists()
            twitter_input = request.POST['twitter']
            if is_valid_link(twitter_input):
                if twitter_exist:
                    twitter = Social_media_links.filter(link_type='twitter')
                    twitter.update(link_url=twitter_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='twitter')
                    messages.success(request, 'Twitter link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='twitter', link_url=twitter_input)
                    # Activity for social_link_add  
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='twitter')
                    messages.success(request, 'Twitter link created successfully')
            else:
                messages.error(request, 'Invalid Twitter link')
        else:
            messages.error(request, 'Please Fill Twitter Input')       

    if 'linkedin' in request.POST:
        if request.POST['linkedin'].strip() != '':
            linkedin_exist = Social_media_links.filter(link_type='linkedin').exists()
            linkedin_input = request.POST['linkedin']
            if is_valid_link(linkedin_input):
                if linkedin_exist:
                    linkedin = Social_media_links.filter(link_type='linkedin')
                    linkedin.update(link_url=linkedin_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='linkedin')
                    messages.success(request, 'LinkedIn link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='linkedin', link_url=linkedin_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='linkedin')
                    messages.success(request, 'LinkedIn link successfully')
            else:
                messages.error(request, 'Invalid LinkedIn link')
        else:
            messages.error(request, 'Please Fill LinkedIn Input')
    
    if 'facebook' in request.POST:
        if request.POST['facebook'].strip() != '':
            facebook_exist = Social_media_links.filter(link_type='facebook').exists()
            facebook_input = request.POST['facebook']
            if is_valid_link(facebook_input):
                if facebook_exist:
                    facebook = Social_media_links.filter(link_type='facebook')
                    facebook.update(link_url=facebook_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='facebook')
                    messages.success(request, 'Facebook link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='facebook', link_url=facebook_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='facebook')  
                    messages.success(request, 'Facebook link successfully')
            else:
                messages.error(request, 'Invalid Facebook link')
        else:
            messages.error(request, 'Please Fill Facebook Input')
    
    if 'instagram' in request.POST:
        if request.POST['instagram'].strip() != '':
            instagram_exist = Social_media_links.filter(link_type='instagram').exists()
            instagram_input = request.POST['instagram']
            if is_valid_link(instagram_input):
                if instagram_exist:
                    instagram = Social_media_links.filter(link_type='instagram')
                    instagram.update(link_url=instagram_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='instagram')
                    messages.success(request, 'Instagram link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='instagram', link_url=instagram_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='instagram')
                    messages.success(request, 'Instagram link successfully')
            else:
                messages.error(request, 'Invalid Instagram link')
        else:
            messages.error(request, 'Please Fill Instagram Input')
    
    if 'snapchat' in request.POST:
        if request.POST['snapchat'].strip() != '':
            snapchat_exist = Social_media_links.filter(link_type='snapchat').exists()
            snapchat_input = request.POST['snapchat']
            if is_valid_link(snapchat_input):
                if snapchat_exist:
                    snapchat = Social_media_links.filter(link_type='snapchat')
                    snapchat.update(link_url=snapchat_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='snapchat')
                    messages.success(request, 'Snapchat link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='snapchat', link_url=snapchat_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='snapchat')
                    messages.success(request, 'Snapchat link successfully')
            else:
                messages.error(request, 'Invalid Snapchat link')
        else:
            messages.error(request, 'Please Fill Snapchat Input')
    
    if 'youtube' in request.POST:
        if request.POST['youtube'].strip() != '':
            youtube_exist = Social_media_links.filter(link_type='youtube').exists()
            youtube_input = request.POST['youtube']
            if is_valid_link(youtube_input):
                if youtube_exist:
                    youtube = Social_media_links.filter(link_type='youtube')
                    youtube.update(link_url=youtube_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='youtube')
                    messages.success(request, 'YouTube link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='youtube', link_url=youtube_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='youtube')
                    messages.success(request, 'YouTube link successfully')
            else:
                messages.error(request, 'Invalid YouTube link')
        else:
            messages.error(request, 'Please Fill YouTube Input')
    
    if 'reddit' in request.POST:
        if request.POST['reddit'].strip() != '':
            reddit_exist = Social_media_links.filter(link_type='reddit').exists()
            reddit_input = request.POST['reddit']
            if is_valid_link(reddit_input):
                if reddit_exist:
                    reddit = Social_media_links.filter(link_type='reddit')
                    reddit.update(link_url=reddit_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='reddit')
                    messages.success(request, 'Reddit link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='reddit', link_url=reddit_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='reddit')
                    messages.success(request, 'Reddit link successfully')
            else:
                messages.error(request, 'Invalid Reddit link')
        else:
            messages.error(request, 'Please Fill Reddit Input')
    
    if 'pinterest' in request.POST:
        if request.POST['pinterest'].strip() != '':
            pinterest_exist = Social_media_links.filter(link_type='pinterest').exists()
            pinterest_input = request.POST['pinterest']
            if is_valid_link(pinterest_input):
                if pinterest_exist:
                    pinterest = Social_media_links.filter(link_type='pinterest')
                    pinterest.update(link_url=pinterest_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='pinterest')
                    messages.success(request, 'Pinterest link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='pinterest', link_url=pinterest_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='pinterest')
                    messages.success(request, 'Pinterest link successfully')
            else:
                messages.error(request, 'Invalid Pinterest link')
        else:
            messages.error(request, 'Please Fill Pinterest Input')
    
    if 'medium' in request.POST:
        if request.POST['medium'].strip() != '':
            medium_exist = Social_media_links.filter(link_type='medium').exists()
            medium_input = request.POST['medium']
            if is_valid_link(medium_input):
                if medium_exist:
                    medium = Social_media_links.filter(link_type='medium')
                    medium.update(link_url=medium_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='medium')
                    messages.success(request, 'Medium link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='medium', link_url=medium_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='medium')
                    messages.success(request, 'Medium link successfully')
            else:
                messages.error(request, 'Invalid Medium link')
        else:
    
            messages.error(request, 'Please Fill Medium Input')
    
    if 'github' in request.POST:
        if request.POST['github'].strip() != '':
            github_exist = Social_media_links.filter(link_type='github').exists()
            github_input = request.POST['github']
            if is_valid_link(github_input):
                if github_exist:
                    github = Social_media_links.filter(link_type='github')
                    github.update(link_url=github_input)
                    # Activity for social_link_update
                    Activity.objects.create(user=user, action_type='social_link_update', linkType='github')
                    messages.success(request, 'GitHub link updated successfully')
                else:
                    SocialMediaLink.objects.create(user=user, link_type='github', link_url=github_input)
                    # Activity for social_link_add
                    Activity.objects.create(user=user, action_type='social_link_add', linkType='github')
                    messages.success(request, 'GitHub link successfully')
            else:
                messages.error(request, 'Invalid GitHub link')
        else:
            messages.error(request, 'Please Fill GitHub Input')
    return redirect(reverse('settings') + f'?tab={current_tab}')

@login_required
def delete_social_link(request, linktype):
    user = request.user
    link_type = linktype
    current_tab = request.GET.get('tab', 'SocialLinks')
    social_media_link_exist = SocialMediaLink.objects.filter(user=user, link_type=link_type).exists()
    if social_media_link_exist:
        social_social_link = SocialMediaLink.objects.filter(user=user, link_type=link_type)
        # Activity for social_link_delete
        Activity.objects.create(user=user, action_type='social_link_delete', linkType=link_type)
        social_social_link.delete()
        messages.success(request, f'{link_type} link deleted successfully')
    else:
        messages.error(request, f'No {link_type} link found')
    return redirect(reverse('settings') + f'?tab={current_tab}')

@login_required
@require_http_methods(['POST'])
def update_user_info(request):
    user = request.user
    current_tab = request.GET.get('tab')
    username = request.POST.get('username').strip()
    first_name = request.POST.get('first_name').strip()
    last_name = request.POST.get('last_name').strip()
    bio = request.POST.get('bio').strip()
    bio1 = re.sub(r'<.*?>', '', bio).replace('&nbsp;', '').strip()
    if bio1 == '':
        print('empty')
        bio1 = None

    if username == '' or first_name == '' or last_name == '':
        messages.error(request, 'Please fill the blank fields')
    elif User.objects.filter(username=username).exclude(id=user.id).exists():
        messages.error(request, 'Username already exists')
    else:
        if user.username == username and user.first_name == first_name and user.last_name == last_name and user.bio in (bio1, bio):
            messages.info(request, 'No changes were made')
        else:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.bio = bio
            if bio1 is None:
                user.bio = None
            else:
                user.bio = bio
            user.save()
            # Activity for user_info_update
            Activity.objects.create(user=user, action_type='user_info_update')
            messages.success(request, 'Profile updated successfully')
    return redirect(reverse('settings') + f'?tab={current_tab}')

@login_required
@require_http_methods(['POST'])
def change_password(request):
    current_tab = request.GET.get('tab')
    old_password = request.POST.get('oldPassword')
    new_password = request.POST.get('newPassword')
    confirm_password = request.POST.get('confirmPassword')
    user = authenticate(request, username=request.user.username, password=old_password)
    if user is not None:
        if new_password == confirm_password:
            if len(new_password) < 8:
                messages.error(request, 'New password must be at least 8 characters long.')
            elif new_password == old_password:
                messages.error(request, 'New password cannot be the same as the old password.')
            else:
                user.set_password(new_password)
                user.save()
                # Activity for password_change
                Activity.objects.create(user=user, action_type='password_change')
                messages.success(request, 'Your password was successfully updated!')
                update_session_auth_hash(request, user)  # Important!
                # Send the successfully reset password message via email
                change_password_message = f"http://127.0.0.1:8000/login/"
                email_content = f"""
                <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    <div style="background-color: #007BFF; color: #ffffff; text-align: center; padding: 20px;">
                        <h1 style="font-size: 24px; font-weight: bold;">Password changed successfully!</h1>
                    </div>
                    <div style="padding: 20px;">
                        <p style="margin-bottom: 16px;">You recently change your password!</p>
                        <p style="margin-bottom: 16px;">To Login to your account , please click the button below:</p>
                        <a href="{change_password_message}" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; transition: background-color 0.2s;">Login to your account</a>
                        <p style="margin-top: 16px;">If you have any questions, feel free to reach out to our support team.</p>
                    </div>
                    <div style="background-color: #f4f4f4; text-align: center; padding: 10px;">
                        <p style="font-size: 12px; color: #777777;">&copy; {current_year} Timber. All rights reserved.</p>
                    </div>
                </div>
                """
                # Create the email message
                email = EmailMessage(
                    subject="Successfully Change Password (computer generated email, don't reply)",
                    body=email_content,
                    from_email="rohitkrgupta8292@gmail.com",
                    to=[user.email],
                )
                # Specify that the email is HTML
                email.content_subtype = "html"  # Set the content type to HTML
                # Send the email
                email.send(fail_silently=False)
                return redirect(reverse('settings') + f'?tab={current_tab}')
        else:
            messages.error(request, 'New password and confirmation do not match.')
    else:
        messages.error(request, 'Old password is incorrect.')
    return redirect(reverse('settings') + f'?tab={current_tab}')

@login_required
def delete_user(request):
    user = request.user
    current_tab = request.GET.get('tab', 'AdvancedSettings')
    if request.method == 'POST':
        delete_user_message = f"http://127.0.0.1:8000/signup/"
        email_content = f"""
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); overflow: hidden;">
            <div style="background-color: #007BFF; color: #ffffff; text-align: center; padding: 20px;">
                <h1 style="font-size: 24px; font-weight: bold;">Account Deleted Successfully!</h1>
            </div>
            <div style="padding: 20px;">
                <p style="margin-bottom: 16px;">You recently deleted your account from Timber. We are sorry to leave you. I hope you will comeback if you need us. Til then we were happy that you are part of our family!</p>
                <p style="margin-bottom: 16px;">To Login to your account , please click the button below:</p>
                <a href="{delete_user_message}" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; transition: background-color 0.2s;">Login to your account</a>
                <p style="margin-top: 16px;">If you have any questions, feel free to reach out to our support team.</p>
            </div>
            <div style="background-color: #f4f4f4; text-align: center; padding: 10px;">
                <p style="font-size: 12px; color: #777777;">&copy; {current_year} Timber. All rights reserved.</p>
            </div>
        </div>
        """
        # Create the email message
        email = EmailMessage(
            subject="Account Deleted (computer generated email, don't reply)",
            body=email_content,
            from_email="rohitkrgupta8292@gmail.com",
            to=[user.email],
        )
        # Specify that the email is HTML
        email.content_subtype = "html"  # Set the content type to HTML
        # Send the email
        email.send(fail_silently=False)
        user.delete()
        messages.success(request, 'Your account has been deleted successfully.')
        return redirect('login')
    return redirect(reverse('settings') + f'?tab={current_tab}')

@login_required
@require_http_methods(["POST"])
def update_profile_banner_image(request):
    user = request.user
    current_tab = request.GET.get('tab')
    # get the image from the form
    if 'profile_picture' in request.FILES or 'banner_image' in request.FILES:
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            try:
                img = Image.open(profile_picture)
                img.verify()
            except IOError:
                messages.error(request, 'Please upload a valid image file')
                return redirect(reverse('settings'))
            if user.profile_picture:
                user.profile_picture.delete()
            user.profile_picture = profile_picture
            user.save()
            # Activity for profile_update
            Activity.objects.create(user=user, action_type='profile_update')
        if 'banner_image' in request.FILES:
            banner_image = request.FILES['banner_image']
            try:
                img = Image.open(banner_image)
                img.verify()
            except IOError:
                messages.error(request, 'Please upload a valid image file')
                return redirect(reverse('settings'))
            if user.banner_image:
                user.banner_image.delete()
            user.banner_image = banner_image
            user.save()
            # Activity for banner_update
            Activity.objects.create(user=user, action_type='banner_update')
        messages.success(request, 'Profile picture/Banner updated successfully')
    else:
        messages.error(request, 'Please upload an image')
    return redirect(reverse('settings') + f'?tab={current_tab}')

@login_required
def delete_banner_image(request):
    user = request.user
    if user.banner_image:
        # Activity for banner_delete
        Activity.objects.create(user=user, action_type='banner_delete')
        user.banner_image.delete()
        messages.success(request, 'Banner image deleted successfully')
    else:
        messages.error(request, 'No banner image to delete')
    return redirect(reverse('settings'))

@login_required
def delete_profile_image(request):
    user = request.user
    if user.profile_picture:
        # Activity for profile_delete
        Activity.objects.create(user=user, action_type='profile_delete')
        user.profile_picture.delete()
        messages.success(request, 'Profile image deleted successfully')
    else:
        messages.error(request, 'No profile image to delete')
    return redirect(reverse('settings'))

@login_required
def user_followers(request, username):
    user = get_object_or_404(User, username=username) 
    sidebar_active_user_follower = request.user == user
    recent_followers = Follow.objects.filter(following=user).order_by('-created_at') # get the followers of the user in recent creation basis 
    oldest_followers = Follow.objects.filter(following=user).order_by('created_at') # get the followers of the user in oldest creation basis
    total_followers = Follow.objects.filter(following=user).count()
    is_follower_recent_users = []
    for follower in recent_followers:
        is_follower_recent_users.append(is_following(request, follower.follower.username))
    # zip followings with is_following_users
    recent_followers_with_is_following = zip(recent_followers, is_follower_recent_users)
    is_follower_oldest_users = []
    for follower in oldest_followers:
        is_follower_oldest_users.append(is_following(request, follower.follower.username))
    # zip followings with is_following_users
    oldest_followers_with_is_following = zip(oldest_followers, is_follower_oldest_users)
    return render(request, "user_followers.html", {"user": user, "current_year": current_year, "recent_followers": recent_followers, "oldest_followers": oldest_followers, "total_followers": total_followers, "recent_followers_with_is_following": recent_followers_with_is_following, "oldest_followers_with_is_following": oldest_followers_with_is_following, "sidebar_active_user_follower": sidebar_active_user_follower})

@login_required
def user_followings(request, username):
    user = get_object_or_404(User, username=username) 
    sidebar_active_user_following = request.user == user
    recent_followings = Follow.objects.filter(follower=user).order_by('-created_at') # get the followers of the user in recent creation basis 
    oldest_followings = Follow.objects.filter(follower=user).order_by('created_at') # get the followers of the user in oldest creation basis
    sidebar_active_following =  request.user == user
    total_followings = Follow.objects.filter(follower=user).count()
    is_following_recent_users = []
    for following in recent_followings:
        is_following_recent_users.append(is_following(request, following.following.username))
    # zip followings with is_following_users
    recent_followings_with_is_following = zip(recent_followings, is_following_recent_users)
    is_following_oldest_users = []
    for following in oldest_followings:
        is_following_oldest_users.append(is_following(request, following.following.username))
    # zip followings with is_following_users
    oldest_followings_with_is_following = zip(oldest_followings, is_following_oldest_users)
    return render(request, "user_followings.html", {"user": user, "current_year": current_year, "recent_followings": recent_followings, "oldest_followings": oldest_followings, "total_followings": total_followings, "recent_followings_with_is_following": recent_followings_with_is_following, "oldest_followings_with_is_following": oldest_followings_with_is_following, "sidebar_active_user_following": sidebar_active_user_following})

@login_required
def user_posts(request, username):
    user = get_object_or_404(User, username=username)
    sidebar_active_user_post = request.user == user
    recent_posts = Post.objects.filter(author=user).order_by('-created_at') # get the posts of
    oldest_posts = Post.objects.filter(author=user).order_by('created_at')
    total_posts = Post.objects.filter(author=user).count()
    return render(request, "user_posts.html", {"user": user, "current_year": current_year, "sidebar_active_user_post":sidebar_active_user_post, "recent_posts":recent_posts, "oldest_posts":oldest_posts, "total_posts":total_posts})

@require_http_methods(['POST'])
@login_required
def follow_unfollow(request, username):
    user = request.user
    following_user = User.objects.get(username=username)

    if user == following_user:
        return JsonResponse({'error': 'You cannot follow yourself'})

    follow, created = Follow.objects.get_or_create(follower=user, following=following_user)

    if created:
        # return JsonResponse({'success': 'You are now following this user'})
        following = True
        # Activity for follow
        Activity.objects.create(user=user, action_type='follow', followed_user=following_user)
        Notification.objects.create(user=following_user, notification_type='follow', follower=user)
    else:
        follow.delete()
        # Activity for unfollow
        Activity.objects.create(user=user, action_type='unfollow', followed_user=following_user)
        Notification.objects.filter(user=following_user, notification_type='follow', follower=user).delete()
        following = False

    return JsonResponse({'success': True, 'following': following})

def privacy_policy(request):
    return render(request, "privacy_policy.html", {"current_year": current_year})

def terms_and_conditions(request):
    return render(request, "terms_and_conditions.html", {"current_year": current_year})

def about_us(request):
    return render(request, "about_us.html", {"current_year": current_year})

# view for forget password
@unauthenticated_user
def forgot_password(request):
    if request.method == "POST":
        username_or_email = request.POST["username_or_email"]
        try:
            if "@" in username_or_email:  # chech it the input is an email
                user = User.objects.get(email=username_or_email)
            else:  # otherwise treat it as a username
                user = User.objects.get(username=username_or_email)
            # Here you can generate a token or a random string to send via email
            token = get_random_string(length=32)
            # Create a PasswordResetToken instance
            PasswordResetToken.objects.create(user=user, token=token)
            # Send the reset link via email
            reset_link = f"http://127.0.0.1:8000/reset_password/{token}/"
            email_content = f"""
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); overflow: hidden;">
                <div style="background-color: #007BFF; color: #ffffff; text-align: center; padding: 20px;">
                    <h1 style="font-size: 24px; font-weight: bold;">Password Reset Link!</h1>
                </div>
                <div style="padding: 20px;">
                    <p style="margin-bottom: 16px;">Your reset password link given below!</p>
                    <p style="margin-bottom: 16px;">To reset your passwrod, please click the button below:</p>
                    <a href="{reset_link}" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; transition: background-color 0.2s;">Reset Your Password</a>
                    <p style="margin-top: 16px;">If you have any questions, feel free to reach out to our support team.</p>
                </div>
                <div style="background-color: #f4f4f4; text-align: center; padding: 10px;">
                    <p style="font-size: 12px; color: #777777;">&copy; {current_year} Timber. All rights reserved.</p>
                </div>
            </div>
            """
            # Create the email message
            email = EmailMessage(
                subject="Reset Password Request (computer generated email, don't reply)",
                body=email_content,
                from_email="rohitkrgupta8292@gmail.com",
                to=[user.email],
            )
            # Specify that the email is HTML
            email.content_subtype = "html"  # Set the content type to HTML
            # Send the email
            email.send(fail_silently=False)

            messages.success(request, "Password reset link sent to your email")
            return redirect("login")
        except ObjectDoesNotExist:
            messages.error(request, "User does not exist")
            return render(request, "forgot_password.html")
    return render(request, "forgot_password.html")

# view for reset password
@unauthenticated_user
def reset_password(request, token):
    try:
        password_reset_token = PasswordResetToken.objects.get(token=token)

        if password_reset_token.is_expired():
            messages.error(request, "Password reset link has expired.")
            return redirect("forget_password")
        # If the token is valid, you can proceed with the password reset process
        if request.method == "POST":
            password1 = request.POST["password1"]  # new password
            password2 = request.POST["password2"]  # confirm password

            if password1 != password2:
                messages.error(request, "Passwords do not match")
                return render(request, "reset_password.html", {"token": token})

            # update the user's password
            user = password_reset_token.user
            user.password = make_password(password1)  # Hash the new password
            user.save()
            # Send the successfully reset password message via email
            reset_password_message = f"http://127.0.0.1:8000/login/"
            email_content = f"""
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); overflow: hidden;">
                <div style="background-color: #007BFF; color: #ffffff; text-align: center; padding: 20px;">
                    <h1 style="font-size: 24px; font-weight: bold;">Password Reset Successfully!</h1>
                </div>
                <div style="padding: 20px;">
                    <p style="margin-bottom: 16px;">You successfully reset your password!</p>
                    <p style="margin-bottom: 16px;">To Login to your account , please click the button below:</p>
                    <a href="{reset_password_message}" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; transition: background-color 0.2s;">Login to your account</a>
                    <p style="margin-top: 16px;">If you have any questions, feel free to reach out to our support team.</p>
                </div>
                <div style="background-color: #f4f4f4; text-align: center; padding: 10px;">
                    <p style="font-size: 12px; color: #777777;">&copy; {current_year} Timber. All rights reserved.</p>
                </div>
            </div>
            """
            # send_mail(
            #     "Successfully Reset Password",  # subject of email
            #     email_content,
            #     "rohitkrgupta8292@gmail.com",
            #     [user.email],
            #     fail_silently=False,
            # )

            # Create the email message
            email = EmailMessage(
                subject="Successfully Reset Password (computer generated email, don't reply)",
                body=email_content,
                from_email="rohitkrgupta8292@gmail.com",
                to=[user.email],
            )
            # Specify that the email is HTML
            email.content_subtype = "html"  # Set the content type to HTML
            # Send the email
            email.send(fail_silently=False)
            # delete the password reset token
            password_reset_token.delete()
            messages.success(request, "Password reset successfully")
            return redirect("login")
        return render(request, "reset_password.html", {"token": token})
    except PasswordResetToken.DoesNotExist:
        messages.error(request, "Invalid password reset link")
        return redirect("forget_password")

# view for signup
@unauthenticated_user
def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        # check if the user already exists
        if (
            User.objects.filter(email=email).exists()
            or User.objects.filter(username=username).exists()
        ):
            messages.error(request, "User/Email already exist")
            return render(request, "signup.html")

        if password1 != password2:
            messages.error(request, "Password do not match.")
            return render(request, "signup.html")

        try:
            user = User.objects.create_user(username, email, password1)
            user.auth_method = "default"
            user.save()
            messages.success(
                request, "Successfully created your account."
            )  # Add success message
            # send mail after creating successfully account
            welcome_link = f"http://127.0.0.1:8000/"
            email_content = f"""
            <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); overflow: hidden;">
                <div style="background-color: #007BFF; color: #ffffff; text-align: center; padding: 20px;">
                    <h1 style="font-size: 24px; font-weight: bold;">Welcome to Our Website!</h1>
                </div>
                <div style="padding: 20px;">
                    <p style="margin-bottom: 16px;">Thank you for creating an account with us. We're excited to have you on board!</p>
                    <p style="margin-bottom: 16px;">To get started, please click the button below:</p>
                    <a href="{welcome_link}" style="display: inline-block; background-color: #007BFF; color: #ffffff; padding: 10px 20px; border-radius: 5px; text-decoration: none; transition: background-color 0.2s;">Visit Us</a>
                    <p style="margin-top: 16px;">If you have any questions, feel free to reach out to our support team.</p>
                </div>
                <div style="background-color: #f4f4f4; text-align: center; padding: 10px;">
                    <p style="font-size: 12px; color: #777777;">&copy; {current_year} Timber. All rights reserved.</p>
                </div>
            </div>
            """
            # send_mail(
            #     "welcome message",
            #     email_content,
            #     "rohitkrgupta8292@gmail.com",
            #     [user.email],
            #     fail_silently=False,
            # )

            # Create the email message
            email = EmailMessage(
                subject="welcome message (computer generated email, don't reply)",
                body=email_content,
                from_email="rohitkrgupta8292@gmail.com",
                to=[user.email],
            )
            # Specify that the email is HTML
            email.content_subtype = "html"  # Set the content type to HTML
            # Send the email
            email.send(fail_silently=False)

            return redirect("login")  # Redirect to login after successfully signup
        except Exception as e:
            messages.error(request, str(e))
            return render(request, "signup.html")
    return render(request, "signup.html")

# view for login
@unauthenticated_user
def user_login(request):
    if request.method == "POST":
        username_or_email = request.POST["username_or_email"]
        password = request.POST["password"]

        # Try to authenticate user
        try:
            if "@" in username_or_email:  # chech it the input is an email
                user = User.objects.get(email=username_or_email)
            else:  # otherwise treat it as a username
                user = User.objects.get(username=username_or_email)
            # authenticate the user
            user = authenticate(username=user.username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')  # Get the stored URL
                if next_url:
                  # del request.session['next']
                  return redirect(next_url)
                return redirect("home")
            else:
                messages.error(request, "Incorrect Password.")
        except ObjectDoesNotExist:
            messages.error(
                request, "User does not exist."
            )  # # user not found will return invalid message
            return render(request, "login.html")
    return render(request, "login.html")

@login_required
def user_logout(request):
    logout(request)
    return redirect("login")