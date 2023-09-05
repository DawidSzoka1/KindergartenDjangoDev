import pytest


@pytest.mark.django_db
def test_parent_profile_access_1(client_conf, client_parent, client_director):
    response = client_conf.get(f"/parent/profile/{client_parent['parent'].id}/")
    assert response.status_code == 302
    response = client_director['client'].get(f"/parent/profile/{client_parent['parent'].id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_parent_profile_access_2(client_parent):
    response_parent = client_parent['client'].get(f"/parent/profile/{client_parent['parent'].id}/")
    assert response_parent.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/parent/profile/{client_parent['parent'].id}/")
    assert response_parent.status_code == 200
