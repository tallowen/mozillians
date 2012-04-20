from nose.tools import eq_

from common.tests import TestCase
from funfactory.urlresolvers import reverse


class TrailingSlashMiddlewareTestCase(TestCase):
    def test_middleware_redirects(self):
        r = self.client.get(reverse('about'))
        no_slash_path = r.request['PATH_INFO']
        r = self.client.get(reverse('about') + u'/', follow=True)
        with_slash_path = r.request['PATH_INFO']
        eq_(no_slash_path, with_slash_path,
            'Both requests should redirect to the same location')

    def test_no_trailing_slash(self):
        r = self.client.get(reverse('about') + u'/', follow=True)
        assert not r.request['PATH_INFO'][-1] in ['/', u'/']
