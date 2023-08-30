import pytest


def test_access(client_conf):
    response = client_conf.get('/list/kids/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_access_director(client_director):
    response = client_director['client'].get('/list/kids/')
    assert response.status_code == 200
