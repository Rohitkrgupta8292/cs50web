from .models import User, Follow, Notification
from django.utils import timezone
import random

def layout_processor(request):
    current_year = timezone.now().year
    def is_following(username):
        if request.user.is_authenticated:
            user = User.objects.get(username=username)
            return Follow.objects.filter(follower=request.user, following=user).exists()
        return False
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(user=request.user, read=False)
        # unread = notifications.exists()
        unread_count = notifications.count()
        users = User.objects.exclude(username=request.user.username)
        random_users = random.sample(list(users), min(4, users.count()))
        random_users_count = User.objects.exclude(username=request.user.username).count()
        is_following_sidebar_users = []
        for user in random_users:
            is_following_sidebar_users.append(is_following(user.username))
        user_following = list(zip(random_users, is_following_sidebar_users))
        return {'random_users': random_users, "random_users_count":random_users_count, 'user_following': user_following, 'unread_count': unread_count, "current_year": current_year}
    return {}