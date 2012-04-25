import os

import random
from string import letters

from django import test
from django.conf import settings
from django.contrib.auth.models import User
from funfactory.urlresolvers import reverse

from elasticutils import get_es


def user(**kwargs):
    defaults = {}
    if 'username' not in kwargs:
        defaults['username'] = ''.join(random.choice(letters) for x in xrange(15))
    if 'email' not in kwargs:
        defaults['email'] = ''.join(random.choice(letters) for x in xrange(15)) \
                                + '@example.com'
    if 'first_name' not in kwargs:
        defaults['first_name'] = ''.join(random.choice(letters) for x in xrange(15))
    if 'last_name' not in kwargs:
        defaults['last_name'] = ''.join(random.choice(letters) for x in xrange(15))
    if 'is_vouched' in kwargs:
        del kwargs['is_vouched']
    defaults.update(kwargs)
    user = User.objects.create(**defaults)
    user.save()
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
