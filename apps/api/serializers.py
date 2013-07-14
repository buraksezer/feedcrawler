from django.forms import widgets
from rest_framework import serializers

class FeedSerializer(serializers.Serializer):
    id = serializers.Field()
    feed_url = serializers.CharField(widget=widgets.Textarea, max_length=100000)
    created_at = serializers.DateTimeField()
    last_sync = serializers.DateTimeField(blank=True)
    tagline = serializers.CharField(widget=widgets.Textarea, max_length=100000)
    title = serializers.CharField(max_length=2048)
    link = serializers.CharField(max_length=2048)
    subtitle = serializers.CharField(max_length=2048)
    slug = serializers.CharField(max_length=2048)