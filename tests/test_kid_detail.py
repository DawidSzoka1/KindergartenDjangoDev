import pytest


@pytest.mark.django_db
def test_access(client_conf):
    response = client_conf.get('/kid/details/4/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_access_2(client_director):
    response_director = client_director['client'].get('/kid/details/4/')
    assert response_director.status_code == 403


@pytest.mark.django_db
def test_access_3(client_director):
    response_director = client_director['client'].get(f"/kid/details/{client_director['kid'].id}/")
    assert response_director.status_code == 200
