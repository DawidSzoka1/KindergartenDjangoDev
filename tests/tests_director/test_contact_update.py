import pytest
from director.models import ContactModel


@pytest.mark.django_db
def test_contact_update_access_get(client_director, client_parent, client_conf):
    contact = ContactModel.objects.get(director=client_director['director'])
    response = client_conf.get(f"/contact/update/{contact.id}/")
    assert response.status_code == 302
    response = client_director['client'].get(f"/contact/update/{contact.id}/")
    assert response.status_code == 200
    response_parent = client_parent['client'].get(f"/contact/update/{contact.id}/")
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_contact_update_access_post(client_director):
    contact = ContactModel.objects.get(director=client_director['director'])
    response = client_director['client'].post(f"/contact/update/{contact.id}/",
                                              {'phone': '+48987654321', 'email_address': 'dawdi@gmail.com',
                                               'localization': 'vcbdf', 'director': client_director['director'].id})
    assert response.status_code == 302
    assert ContactModel.objects.get(director=client_director['director']).phone == '+48987654321'

