from django.contrib.auth.models import AbstractUser
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill, ResizeToFit, SmartResize
from django.db import models
from django.utils import timezone
from datetime import timedelta
from tinymce.models import HTMLField  # Import HTMLField from tinymce
from django.utils.html import strip_tags
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.urls import reverse

class User(AbstractUser):
    # you can add additional fields here if needed
    bio = models.TextField(max_length=2000, blank=True, null=True)
    profile_picture = ProcessedImageField(upload_to='profile_pictures/', processors=[ResizeToFill(300,300)], format='JPEG', options={'quality':80}, blank=True, null=True)
    banner_image = ProcessedImageField(upload_to='banners/', processors=[ResizeToFit(1200,600)], format='JPEG', options={'quality':80}, blank=True, null=True)  #  banner field
    AUTH_METHOD_CHOICES = (
        ('default', 'Default'),
        ('google', 'Google'),
        ('github', 'GitHub'),
    )
    auth_method = models.CharField(max_length=10, choices=AUTH_METHOD_CHOICES, default='default')

    def __str__(self):
        return f"{self.username} ({self.email})"
    
    def get_absolute_url(self):
        return reverse('user_profile', args=[self.username])

class SearchQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.query    

class SocialMediaLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    link_type = models.CharField(max_length=255, choices=[
        ('twitter', 'Twitter'),
        ('linkedin', 'LinkedIn'),
        ('github', 'GitHub'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('youtube', 'YouTube'),
        ('reddit', 'Reddit'),
        ('pinterest', 'Pinterest'),
        ('medium', 'Medium'),
        ('snapchat', 'Snapchat'),
    ])
    link_url = models.URLField()
    
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.name}"

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"#{self.name}"

class Post(models.Model):
    title = models.CharField(max_length=200)
    content = HTMLField()  # Use HTMLField for rich text editing
    # content = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)  # New slug field
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')  # Updated to ManyToManyField
    thumbnail = ProcessedImageField(upload_to='thumbnails/', processors=[ResizeToFit(300,300)], format='JPEG', options={'quality':80}, blank=True, null=True)  # New thumbnail field

    def __str__(self):
        return f"{self.title}"
    def save(self, *args, **kwargs):
        # Generate slug if it's not provided
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    def get_limited_content(self):
        # Limit content to 15 words
        plain_text = strip_tags(self.content)  # Remove HTML tags
        return mark_safe(' '.join(plain_text.split()[:15]) + ('...' if len(plain_text.split()) > 15 else ''))
    def get_absolute_url(self):
        return reverse('post_detail', args=[self.slug])

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('user', 'post')  # Ensure a user can like a post only once

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.title} that is a reply to {self.parent.author.username if self.parent else 'the post itself'}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('reply', 'Reply'),
        ('reply1', 'Reply1'),
        ('follow', 'Follow'),
        ('post', 'Post'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True)
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor_notifications', blank=True, null=True)
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_notifications', blank=True, null=True)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} got {self.notification_type} notification'

class Activity(models.Model):
    ACTION_TYPES = (
        ('post_create', 'Post Created'),
        ('post_update', 'Post Updated'),
        ('post_like', 'Post Liked'),
        ('post_unlike', 'Post Unliked'),
        ('post_comment', 'Post Commented'),
        ('post_reply', 'Post Replied'),
        ('follow', 'Followed'),
        ('unfollow', 'Unfollowed'),
        ('profile_update', 'Profile Updated'),
        ('profile_delete', 'Profile Deleted'),
        ('banner_update', 'Banner Updated'),
        ('banner_delete', 'Banner Deleted'),
        ('user_info_update', 'User Info Updated'),
        ('password_change', 'Password Changed'),
        ('social_link_add', 'Social Link Added'),
        ('social_link_update', 'Social Link Updated'),
        ('social_link_delete', 'Social Link Deleted'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True)
    followed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followed_user', null=True, blank=True)
    linkType = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.action_type}'

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=200, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=1)
    def __str__(self):
        return f"Token for {self.user}"