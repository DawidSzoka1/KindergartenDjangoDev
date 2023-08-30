import pytest

from children.models import Kid


@pytest.mark.django_db
def test_delete_access(client_director):
    response = client_director['client'].get(f"/kid/delete/{client_director['kid'].id}/")
    assert response.status_code == 403
    response = client_director['client'].get(f"/kid/delete/4/")
    assert response.status_code == 403
    client_director['client'].logout()
    response = client_director['client'].get(f"/kid/delete/{client_director['kid'].id}/")
    assert response.status_code == 302



@pytest.mark.django_db
def test_delete_access(client_director):
    assert Kid.objects.filter(id=client_director['kid'].id).first().is_active
    response = client_director['client'].post(f"/kid/delete/{client_director['kid'].id}/")
    assert response.status_code == 302
    assert Kid.objects.filter(id=client_director['kid'].id).first().is_active == False
