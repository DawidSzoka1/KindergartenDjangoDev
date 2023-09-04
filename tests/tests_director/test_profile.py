import pytest


@pytest.mark.django_db
def test_profile_access(client_director):
    response = client_director['client'].get('/director/profile/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_profile_access_2(client_conf, client_parent):
    response = client_conf.get('/director/profile/')
    assert response.status_code == 302
    response = client_parent['client'].get('/director/profile/')
    assert response.status_code == 403


