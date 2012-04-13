from django.contrib.auth.models import User

from common.tests import TestCase

from funfactory.urlresolvers import reverse
from nose.tools import eq_
from pyquery import PyQuery as pq

from groups.models import Group


class PrivacyTest(TestCase):

    def setUp(self):
        super(PrivacyTest, self).setUp()
        normal_group = Group.objects.create(name='cheesezilla')
        self.mozillian.get_profile().groups.add(normal_group)

        self.vouched_user = User.objects.create(
                            username='vouchify',
                            last_name='likeaboss',
                            email='vouch@example.com')
        vouched_profile = self.vouched_user.get_profile()
        vouched_profile.is_vouched = True
        vouched_profile.save()

    def test_public_page_works(self):
        mozillian_profile = self.mozillian.get_profile()
        mozillian_profile.basic_info_privacy = 'PB'
        mozillian_profile.save()
        self.client.logout()
        r = self.client.get(reverse('profile', args=[self.mozillian.username]))
        eq_(r.status_code, 200, 'Logged out user should see public profile.')
        doc = pq(r.content)
        eq_(doc('#profile-info .p-name').text(),
            mozillian_profile.display_name, 'We should see the right profile.')

        #
        mozillian_profile.basic_info_privacy = 'VO'
        mozillian_profile.save()

    def test_non_public_page_gives_404(self):
        mozillian_profile = self.mozillian.get_profile()
        mozillian_profile.basic_info_privacy = 'VO'
        mozillian_profile.save()
        self.client.logout()
        r = self.client.get(reverse('profile', args=[self.mozillian.username]))
        eq_(r.status_code, 404, 'Logged out user not see private profile')

    def test_vouched_users_can_see_private_profiles(self):
        # Create a vouched user to explore with
        mozillian_profile = self.mozillian.get_profile()
        mozillian_profile.basic_info_privacy = 'VO'
        mozillian_profile.save()
        self.client.logout()
        r = self.client.get(reverse('profile', args=[self.mozillian.username]))
        eq_(r.status_code, 404, 'Logged out user not see private profile')
        self.client.login(email=self.vouched_user.email)
        r = self.client.get(reverse('profile', args=[self.mozillian.username]))
        eq_(r.status_code, 200, 'We should see the right profile.')
        eq_(pq(r.content)('#profile-info .p-name').text(),
            mozillian_profile.display_name, 'We should see the right profile.')

    def test_change_other_options(self):
        mozillian_profile = self.mozillian.get_profile()
        mozillian_profile.basic_info_privacy = 'PB'
        mozillian_profile.contact_info_privacy = 'PB'
        mozillian_profile.tags_privacy = 'PB'
        mozillian_profile.save()
        self.client.logout()
        r = self.client.get(reverse('profile', args=[self.mozillian.username]))
        assert (self.mozillian.email in pq(r.content)(r'#profile-info').text(),
                'Email should be in profile view.')
        assert pq(r.content)('#groups'), 'Groups should be visable.'
        mozillian_profile.contact_info_privacy = 'VO'
        mozillian_profile.tags_privacy = 'VO'
        mozillian_profile.save()

        r = self.client.get(reverse('profile', args=[self.mozillian.username]))
        assert ((not self.mozillian.email in
                 pq(r.content)(r'#profile-info').text()),
                 'Email should not be in profile view.')
        assert not pq(r.content)('#groups'), 'Groups should not be visable.'
