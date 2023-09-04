import pytest


@pytest.mark.django_db
def test_group_details_access(client_director, client_conf):
    response = client_director['client'].get(f"/group/details/{client_director['group'].id}/")
    assert response.status_code == 200
    response = client_conf.get(f"/group/details/{client_director['group'].id}/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_group_details_access_2(client_director, client_parent):
    response_parent = client_parent['client'].get(f"/group/details/{client_director['group'].id}/")
    assert response_parent.status_code == 403
    response_parent = client_parent['client'].get(f"/group/details/{client_parent['group'].id}/")
    assert response_parent.status_code == 200
