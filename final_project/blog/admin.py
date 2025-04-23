from django.contrib import admin
from .models import User, Post, PasswordResetToken, Category, Tag,  Comment, Like, SocialMediaLink, Follow, Notification, SearchQuery, Activity
from tinymce.widgets import TinyMCE
from django import forms

# Register your models here.
class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30}),  # Use TinyMCE widget for the content field
        }

class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'
        widgets = {
            'bio': TinyMCE(attrs={'cols': 80, 'rows': 30}),
        }

class UserAdmin(admin.ModelAdmin):
    form = UserAdminForm

class SocialMediaLinkAdmin(admin.ModelAdmin):
    list_display = ('user', 'link_type', 'link_url')
    list_filter = ('user', 'link_type')
    search_fields = ('user__username', 'link_url')

admin.site.register(SocialMediaLink, SocialMediaLinkAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(PasswordResetToken)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(Like)
admin.site.register(Follow)
admin.site.register(Notification)
admin.site.register(SearchQuery)
admin.site.register(Activity)

