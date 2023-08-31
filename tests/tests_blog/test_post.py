import pytest


@pytest.mark.django_db
def test_post_access(client_conf):
    response = client_conf.get('/wydarzenia/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_post_access_2(client_director):
    response_logged = client_director['client'].get('/wydarzenia/')
    assert response_logged.status_code == 200
