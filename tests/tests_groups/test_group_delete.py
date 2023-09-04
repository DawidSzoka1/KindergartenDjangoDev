import pytest

from groups.models import Groups


@pytest.mark.django_db
def test_group_delete_access_get(client_director, client_conf, client_parent):
    response = client_director['client'].get(f"/group/delete/{client_director['group'].id}/")
    assert response.status_code == 403
    response = client_conf.get(f"/group/delete/{client_director['group'].id}/")
    assert response.status_code == 302
    response_parent = client_parent['client'].get(f"/group/delete/{client_director['group'].id}/")
    assert response_parent.status_code == 403
    response_parent = client_parent['client'].get(f"/group/delete/{client_parent['group'].id}/")
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_group_delete_access_post(client_director, client_parent, client_conf):
    response = client_director['client'].post(f"/group/delete/{client_director['group'].id}/")
    assert response.status_code == 302
    assert not Groups.objects.get(id=client_director['group'].id).is_active
    response = client_conf.post(f"/group/delete/{client_director['group'].id}/")
    assert response.status_code == 302
    response_parent = client_parent['client'].post(f"/group/delete/{client_director['group'].id}/")
    assert response_parent.status_code == 403
    response_parent = client_parent['client'].post(f"/group/delete/{client_parent['group'].id}/")
    assert response_parent.status_code == 403
