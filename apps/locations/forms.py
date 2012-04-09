from django import forms

from tower import ugettext_lazy as _lazy

from locations.models import Country


class AddressForm(forms.ModelForm):

    first_name = forms.CharField(label=_lazy(u'First Name'), max_length=30,
                                                             required=False)

    #: L10n: Street address; not entire address
    street = forms.CharField(label=_lazy(u'Address'), required=False)
    city = forms.CharField(label=_lazy(u'City'), required=False)
    # TODO: Add validation of states/provinces/etc. for known/large countries.
    province = forms.CharField(label=_lazy(u'Province/State'), required=False)
    postal_code = forms.CharField(label=_lazy(u'Postal/Zip Code'),
                                  required=False)

    def __init__(self, *args, **kwargs):
        """Add a locale-aware list of countries to the form."""
        locale = kwargs.get('locale', 'en-US')
        if kwargs.get('locale'):
            del kwargs['locale']

        instance = kwargs.get('instance')
        if instance:
            initial = kwargs.get('initial', {})
            if instance.postal_code:
                initial.update(postal_code=instance.postal_code.code)

            kwargs['initial'] = initial

        super(AddressForm, self).__init__(*args, **kwargs)

        self.fields['country'] = forms.ChoiceField(label=_lazy(u'Country'),
                required=False, choices=([['', '--']] +
                                         Country.localized_list(locale)))

    def clean_country(self):
        """Return a country object for the country selected (None if empty)."""
        if not self.cleaned_data['country']:
            return None

        country = Country.objects.filter(id=self.cleaned_data['country'])
        return country[0] if country else None
