from django import forms
from django.utils.translation import ugettext_lazy as _
from userena import settings as userena_settings


class AuthenticationForm(forms.Form):
    """
    A custom form where the identification can be a e-mail address or username.

    """
    identification = forms.CharField(widget=forms.TextInput(attrs={'class': 'required', 'placeholder': 'Email or username'}),
        max_length=75,
        error_messages={'required': _("%(error)s") % {'error': "Either supply us with your email or username."}})

    password = forms.CharField(label=_("Password"),
                               widget=forms.PasswordInput(attrs={'class': 'required', 'placeholder': 'Password'}, render_value=False))
    remember_me = forms.BooleanField(widget=forms.CheckboxInput(),
                                     required=False,
                                     label=_(u'Remember me for %(days)s') % {'days': _(userena_settings.USERENA_REMEMBER_ME_DAYS[0])})

    def __init__(self, *args, **kwargs):
        """ A custom init because we need to change the label if no usernames is used """
        super(AuthenticationForm, self).__init__(*args, **kwargs)
        # Dirty hack, somehow the label doesn't get translated without declaring
        # it again here.
        self.fields['remember_me'].label = _(u'Remember me')
        if userena_settings.USERENA_WITHOUT_USERNAMES:
            identification = forms.CharField(widget=forms.TextInput(attrs={'class': 'required', 'placeholder': 'Email or username'}),
                max_length=75,
                error_messages={'required': _("%(error)s") % {'error': "Either supply us with your email or username."}})