from django import forms


class SubscribeForm(forms.Form):
    feed_url = forms.CharField(label="New subscription", max_length=256, \
        widget=forms.TextInput(attrs={'type': "text", "placeholder": 'Give a valid URL'}))
    #tags = forms.CharField(max_length=512, required=False)


class FeedSearchForm(forms.Form):
    feed_search = forms.CharField(label="Search in your subscriptions", max_length=1024, \
        widget=forms.TextInput(attrs={"type": "text", 'placeholder':'URL or title'}))

#class AuthenticationForm(forms.Form):
#    """
#    Base class for authenticating users. Extend this to get a form that accepts
#    username/password logins.
#    """
#    username = forms.CharField(label="Username", max_length=30)
#    password = forms.CharField(label="Password", widget=forms.PasswordInput)
