from django.db import models
from django.contrib.auth.models import User

from django.template.defaultfilters import slugify


class Feed(models.Model):
    feed_url = models.CharField(unique=True, max_length=512)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sync = models.DateTimeField(null=True)
    users = models.ManyToManyField(User)


class Post(models.Model):
    title = models.CharField(max_length=1024)
    content = models.TextField()
    link = models.URLField(max_length=512)
    created_at = models.DateField()
    # In fact, parser_id is the same thing with post's URL
    parser_id = models.URLField(unique=True, max_length=512)
    # slug value must be prepared using title value
    slug = models.SlugField(unique=True, blank=True)
    feed = models.ForeignKey(Feed)

    def save(self, *args, **kwargs):
        if not self.id:
            # Newly created object, so set slug
            self.slug = slugify(self.title)
            super(Post, self).save(*args, **kwargs)


class Comment(models.Model):
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    post = models.OneToOneField(Post)
    user = models.OneToOneField(User)

"""
Feed
    * id
    * feed URL
    * created_at
    * updated_at
    ** Many to many relationship with User profiles
Post
    * id
    * title
    * content
    * link
    * updated_at
    * parser_id
    ** Many to one relationship with Feed table
Comment
    * id
    * content
    ** One to One relationship with Post table
    ** One to one relationship with User profiles
"""
