from nose.tools import eq_
from pyquery import PyQuery as pq

from django.conf import settings

from common.tests import ESTestCase
from elasticutils import get_es
from funfactory.urlresolvers import reverse

from users.models import UserProfile
from phonebook.tests import user


class TestSearch(ESTestCase):

    def test_search_with_space(self):
        """Extra spaces should not impact search queries."""
        amanda = 'Amanda Younger'
        amandeep = 'Amandeep McIlrath'

        url = reverse('search')
        r = self.mozillian_client.get(url, dict(q='Am'))
        rs = self.mozillian_client.get(url, dict(q=' Am'))

        eq_(r.status_code, 200)
        peeps = r.context['people']
        peeps_ws = rs.context['people']
        saw_amanda = saw_amandeep = False

        for person in peeps:
            if person.display_name == amanda:
                saw_amanda = True
            elif person.display_name == amandeep:
                saw_amandeep = True
            if saw_amanda and saw_amandeep:
                break

        assert peeps[0].id in (peeps_ws[0].id, peeps_ws[1].id)
        self.assertTrue(saw_amanda, 'We see first person')
        self.assertTrue(saw_amandeep, 'We see another person')

    def test_nonvouched_search(self):
        """Make sure that only non vouched users are returned on search."""
        amanda = 'Amanda Younger'
        amandeep = 'Amandeep McIlrath'

        user(first_name='Amanda', last_name='Unvouched')

        if not settings.ES_DISABLED:
            get_es().refresh(settings.ES_INDEXES['default'], timesleep=0)

        url = reverse('search')
        r = self.mozillian_client.get(url, dict(q='Am'))
        rnv = self.mozillian_client.get(url, dict(q='Am', nonvouched_only=1))

        eq_(r.status_code, 200)
        peeps = r.context['people']
        peeps_nv = rnv.context['people']

        saw_amanda = saw_amandeep = False

        for person in peeps:
            if person.display_name == amandeep:
                assert person.is_vouched, 'Amanda is a Mozillian'
                saw_amandeep = True
            elif person.display_name == amanda:
                if person.is_vouched:
                    self.fail('Amandeep should have pending status')
                saw_amanda = True
            if saw_amanda and saw_amandeep:
                break

        self.assertEqual(peeps_nv[0].display_name, amanda)
        self.assertTrue(saw_amanda, 'We see vouched users')
        self.assertTrue(saw_amandeep, 'We see non-vouched users')
        assert all(not person.is_vouched for person in peeps_nv)

    def test_profilepic_search(self):
        """Make sure searching for only users with profile pics works."""

        user(first_name='Aman', vouched=True, photo=True)
        user(first_name='Amanda', vouched=True, photo=True)
        u = user(firset_name='Amihuman', vouched=True)

        self.client.login(email=u.email)

        url = reverse('search')

        r_pics_only = self.client.get(url, dict(q='Am', picture_only=1))
        eq_(r_pics_only.status_code, 200)
        pics_only_peeps = r_pics_only.context['people']
        for person in pics_only_peeps:
            assert person.photo, 'Every person should have a photo'

        r = self.client.get(url, dict(q='Am'))
        eq_(r.status_code, 200)
        peeps = r.context['people']
        # Make sure u shows up in normal search
        assert u.username in [p.username for p in peeps]
        # Make sure u doesn't show up in picture only search
        assert u.username not in [p.username for p in pics_only_peeps]

    def test_mozillian_search_pagination(self):
        """Tests the pagination on search.

        1. assumes no page is passed, but valid limit is passed
        2. assumes invalid page is passed, no limit is passed
        3. assumes valid page is passed, no limit is passed
        4. assumes valid page is passed, valid limit is passed
        """
        url = reverse('search')
        r = self.mozillian_client.get(url, dict(q='Amand', limit='1'))
        peeps = r.context['people']
        self.assertEqual(len(peeps), 1)

        r = self.mozillian_client.get(url, dict(q='Amand', page='test'))
        peeps = r.context['people']
        self.assertEqual(len(peeps), 2)

        r = self.mozillian_client.get(url, dict(q='Amand', page='1'))
        peeps = r.context['people']
        self.assertEqual(len(peeps), 2)

        r = self.mozillian_client.get(url, dict(q='Amand', page='test',
                                                limit='1'))
        peeps = r.context['people']
        self.assertEqual(len(peeps), 1)

        r = self.mozillian_client.get(url, dict(q='Amand', page='test',
                                                limit='x'))
        peeps = r.context['people']
        self.assertEqual(len(peeps), 2)

        r = self.mozillian_client.get(url, dict(q='Amand', page='test',
                                                limit='-3'))
        peeps = r.context['people']
        self.assertEqual(len(peeps), 2)

    def test_empty_query_search(self):
        """Make sure the search method works with an empty query"""
        assert UserProfile.search('').count()

    def test_proper_url_arg_handling(self):
        """Make sure URL arguments are handled correctly"""
        #Create a new unvouched user
        user()

        if not settings.ES_DISABLED:
            get_es().refresh(settings.ES_INDEXES['default'], timesleep=0)

        search_url = reverse('search')
        r = self.mozillian_client.get(search_url)
        assert not pq(r.content)('.result')

        r = self.mozillian_client.get(search_url,
                                      dict(q=u'', nonvouched_only=1))

        assert pq(r.content)('.result')

    def test_single_result(self):
        """Makes sure the client is redirected to the users page
        if they are the only result returned by the query.
        """
        u = user(first_name='Findme', last_name='Ifyoucan')
        client = self.client.login(u=user(vouched=True).email)

        r = client.get(reverse('search'), dict(q='Fin', nonvouched_only=1),
                       follow=True)

        eq_(r.status_code, 200)

        eq_(u.get_profile().display_name,
            pq(r.content)('#profile-info h2').text(),
            'Should be redirected to a user with the right name')
