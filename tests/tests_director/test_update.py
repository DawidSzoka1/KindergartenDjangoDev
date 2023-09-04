import pytest

from director.models import Director


@pytest.mark.django_db
def test_update_access_get(client_director, client_conf, client_parent):
    response = client_director['client'].get('/director/update/')
    assert response.status_code == 200
    response = client_conf.get('/director/update/')
    assert response.status_code == 302
    response = client_parent['client'].get('/director/update/')
    assert response.status_code == 403


@pytest.mark.django_db
def test_update_access_post(client_director):
    response = client_director['client'].post('/director/update/',
                                              {'first_name': 'change', 'last_name': 'last_name', 'gender': 1,
                                               'user': client_director['user'].id})
    assert response.status_code == 302
    assert Director.objects.get(id=client_director['director'].id).first_name == 'change'
