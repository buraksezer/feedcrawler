from django import forms


class SubscribeForm(forms.Form):
    feed_url = forms.CharField(max_length=256, \
        widget=forms.TextInput(attrs={'autocomplete':'off', 'data-provide':'typeahead'}))
    tags = forms.CharField(max_length=512, required=False)


#class AuthenticationForm(forms.Form):
#    """
#    Base class for authenticating users. Extend this to get a form that accepts
#    username/password logins.
#    """
#    username = forms.CharField(label="Username", max_length=30)
#    password = forms.CharField(label="Password", widget=forms.PasswordInput)
