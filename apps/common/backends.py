import base64
import hashlib

from django.contrib.auth.models import User

import commonware.log
from django_browserid.auth import BrowserIDBackend

from Users.models import EmailAddress

log = commonware.log.getLogger('b.common')


def get_username(email):
    return 'u/{0}'.format(base64.urlsafe_b64encode(
            hashlib.sha1(email).digest()).rstrip('='))


class MozilliansBrowserID(BrowserIDBackend):
    """
    Special auth backend to allow registration to work without a current
    assertion. This is dangerous. Don't use authenticated_email unless you've
    just verified somebody.
    """
    supports_inactive_user = False

    def authenticate(self, assertion=None, audience=None, authenticated_email=None):
        if authenticated_email:
            import ipdb; ipdb.set_trace()
            return EmailAddress.objects.get(email=authenticated_email).profile.user

        return super(MozilliansBrowserID, self).authenticate(
                                        assertion=assertion, audience=audience)

    def create_user(self, email):
        import ipdb; ipdb.set_trace()
        user = User.objects.create_user(get_username(email), email)
        EmailAddress.objects.create(profile=user.get_profile(), email=email)
        return user

    def filter_users_by_email(self, email):
        return [e.profile.user for e in EmailAddress.objects.filter(email=email)]


class TestBackend(object):
    """Testing backend that does no real authentication. Great for gags."""
    supports_inactive_user = True

    def authenticate(self, email=None, username=None, password=None):
        if not email:
            email = username
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            pass

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
