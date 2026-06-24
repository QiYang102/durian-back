from model_bakery import baker
from datetime import datetime
from django.test import Client
from django.utils.http import urlencode
from django.urls import reverse

from .models import Tenant, User


def django_extensions_db_fields_func():
    return datetime.now()


baker.generators.add('django_extensions.db.fields.CreationDateTimeField', django_extensions_db_fields_func)
baker.generators.add('django_extensions.db.fields.ModificationDateTimeField', django_extensions_db_fields_func)


def setup_test():
    # tenants
    tenant = baker.make(Tenant, _fill_optional=True)

    # user
    username, password = 'test', 'password'
    user = User(username=username, password=password)
    user.set_password(password)
    user.tenant = tenant
    user.save()

    # initialize the APIClient app
    client = Client()
    client.login(username=username, password=password)

    return client, user, tenant


def url_reverse(viewname, kwargs=None, query_kwargs=None):
    """
    Custom reverse to add a query string after the url
    Example usage:
    url = my_reverse('my_test_url', kwargs={'pk': object.id}, query_kwargs={'next': reverse('home')})
    """
    url = reverse(viewname, kwargs=kwargs)

    if query_kwargs:
        return u'%s?%s' % (url, urlencode(query_kwargs))

    return url
