import pytest
from meals.models import Meals


@pytest.mark.django_db
def test_meal_delete_access_get(client_conf, client_parent, client_director):
    response = client_conf.get(f"/meals/delete/{client_director['meal'].id}/")
    assert response.status_code == 302
    response_dir = client_director['client'].get(f"/meals/delete/{client_director['meal'].id}/")
    assert response_dir.status_code == 403
    response_parent = client_parent['client'].get(f"/meals/delete/{client_director['meal'].id}/")
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_meal_delete_access_post(client_director, client_parent):
    response = client_director['client'].post(f"/meals/delete/{client_director['meal'].id}/")
    assert response.status_code == 302
    assert not Meals.objects.filter(id=client_director['meal'].id).first()
    response_parent = client_parent['client'].post(f"/meals/delete/{client_director['meal'].id}/")
    assert response_parent.status_code == 403
