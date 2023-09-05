import pytest
from parent.models import ParentA


@pytest.mark.django_db
def test_parent_delete_access_get(client_conf, client_parent, client_director):
    response = client_conf.get(f"/parent/delete/{client_parent['kid'].id}/")
    assert response.status_code == 302
    response = client_director['client'].get(f"/parent/delete/{client_parent['parent'].id}/")
    assert response.status_code == 403
    response_parent = client_parent['client'].get(f"/parent/delete/{client_parent['parent'].id}/")
    assert response_parent.status_code == 403
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/parent/delete/{client_parent['parent'].id}/")
    assert response_parent.status_code == 403
    response = client_director['client'].get(f"/parent/delete/{client_parent['parent'].id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_parent_delete_access_post(client_parent):
    assert ParentA.objects.filter(id=client_parent['parent'].id).first()
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response = client_parent['client'].post(f"/parent/delete/{client_parent['parent'].id}/")
    assert response.status_code == 302
    assert not ParentA.objects.filter(id=client_parent['parent'].id).first()
