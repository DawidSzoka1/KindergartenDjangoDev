import pytest


@pytest.mark.django_db
def test_meals_access_1(client_conf, client_director):
    response = client_conf.get(f"/meals/details/{client_director['meal'].id}/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_meals_access_2(client_director, client_parent):
    response = client_director['client'].get(f"/meals/details/{client_director['meal'].id}/")
    assert response.status_code == 200
    response_parent = client_parent['client'].get(f"/meals/details/{client_director['meal'].id}/")
    assert response_parent.status_code == 403
