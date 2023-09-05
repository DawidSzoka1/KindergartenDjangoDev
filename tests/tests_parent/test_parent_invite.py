import pytest
from parent.models import ParentA


@pytest.mark.django_db
def test_parent_invite_access_get(client_conf, client_parent, client_director):
    response = client_conf.get(f"/invite/parent/{client_parent['kid'].id}/")
    assert response.status_code == 302
    response = client_director['client'].get(f"/invite/parent/{client_parent['kid'].id}/")
    assert response.status_code == 403
    response_parent = client_parent['client'].get(f"/invite/parent/{client_parent['kid'].id}/")
    assert response_parent.status_code == 403
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/invite/parent/{client_parent['kid'].id}/")
    assert response_parent.status_code == 200
    response = client_director['client'].get(f"/invite/parent/{client_director['kid'].id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_parent_invite_access_post(client_director):
    response = client_director['client'].post(f"/invite/parent/{client_director['kid'].id}/",
                                              {'email': 'email@gmail.com'})
    assert response.status_code == 302
    assert ParentA.objects.get(user__email='email@gmail.com')
