import os

import random
from string import letters

from django import test
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from funfactory.urlresolvers import reverse

from elasticutils import get_es


def user(**kwargs):
    profile_changes = {}
    if 'username' not in kwargs:
        kwargs['username'] = ''.join(
            random.choice(letters) for x in xrange(15))
    if 'email' not in kwargs:
        kwargs['email'] = ''.join(
            random.choice(letters) for x in xrange(15)) + '@example.com'
    if 'first_name' not in kwargs:
        kwargs['first_name'] = ''.join(
            random.choice(letters) for x in xrange(15))
    if 'last_name' not in kwargs:
        kwargs['last_name'] = ''.join(
            random.choice(letters) for x in xrange(15))

    if 'vouched' in kwargs:
        profile_changes['vouched'] = kwargs['vouched']
        del kwargs['vouched']
    if 'photo' in kwargs:
        profile_changes['photo'] = kwargs['photo']
        del kwargs['photo']
    user = User.objects.create(**kwargs)
    user.save()

    if profile_changes:
        profile = user.get_profile()

        if 'vouched' in profile_changes:
            profile.is_vouched = profile_changes['vouched']

        if 'photo' in profile_changes:
            if profile_changes['photo']:
                with open(os.path.join(os.path.dirname(__file__),
                          'profile-photo.jpg')) as f:
                    profile.photo = File(f)
                    profile.save()  # Must save inside with block

        profile.save()

    if not settings.ES_DISABLED:
        get_es().refresh(settings.ES_INDEXES['default'], timesleep=0)
    return user


def vouch(user):
    profile = user.get_profile()
    profile.is_vouched = True
    profile.save()


def add_profilepic(user):
    client = test.Client()

    client.login(email=user.email)

    with open(os.path.join(os.path.dirname(__file__), 'profile-photo.jpg')) as f:
        r = client.post(reverse('profile.edit'),
            dict(first_name=user.first_name, last_name=user.last_name, photo=f))

    if not settings.ES_DISABLED:
            get_es().refresh(settings.ES_INDEXES['default'], timesleep=0)

    client.logout()
