import pytest


def test_meals_access_1(client_conf):
    response = client_conf.get('/list/meals/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_meals_access_2(client_director, client_parent):
    response = client_director['client'].get('/list/meals/')
    assert response.status_code == 200
    response_parent = client_parent['client'].get('/list/meals/')
    assert response_parent.status_code == 403
