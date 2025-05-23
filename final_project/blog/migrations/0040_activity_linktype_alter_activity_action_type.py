# Generated by Django 5.0.3 on 2025-03-02 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0039_remove_activity_linktype'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='linkType',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='activity',
            name='action_type',
            field=models.CharField(choices=[('post_create', 'Post Created'), ('post_update', 'Post Updated'), ('post_delete', 'Post Deleted'), ('post_like', 'Post Liked'), ('post_unlike', 'Post Unliked'), ('post_comment', 'Post Commented'), ('post_reply', 'Post Replied'), ('follow', 'Followed'), ('unfollow', 'Unfollowed'), ('profile_update', 'Profile Updated'), ('profile_delete', 'Profile Deleted'), ('banner_update', 'Banner Updated'), ('banner_delete', 'Banner Deleted'), ('user_info_update', 'User Info Updated'), ('password_change', 'Password Changed'), ('social_link_add', 'Social Link Added'), ('social_link_update', 'Social Link Updated'), ('social_link_delete', 'Social Link Deleted')], max_length=20),
        ),
    ]
