import pytest
from parent.models import ParentA


@pytest.mark.django_db
def test_parent_update_access_get(client_conf, client_parent, client_director):
    response = client_conf.get(f"/parent/update/{client_parent['parent'].id}/")
    assert response.status_code == 302
    response = client_director['client'].get(f"/parent/update/{client_parent['parent'].id}/")
    assert response.status_code == 403
    response_parent = client_parent['client'].get(f"/parent/update/{client_parent['parent'].id}/")
    assert response_parent.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/parent/update/{client_parent['parent'].id}/")
    assert response_parent.status_code == 403
    response = client_director['client'].get(f"/parent/update/{client_parent['parent'].id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_parent_update_access_post(client_parent):
    response = client_parent['client'].post(f"/parent/update/{client_parent['parent'].id}/",
                                            {
                                                'kids': client_parent['kid'].id,
                                                'principal': client_parent['parent'].principal.first().id,
                                                'user': client_parent['parent'].user.id,
                                                'first_name': 'change',
                                                'last_name': 'change',
                                                'gender': 1,
                                                'city': 'miasto',
                                                'address': 'address',
                                                'zip_code': '15-505',
                                                'phone': '+48987654323'
                                            })
    assert response.status_code == 302
    assert ParentA.objects.get(id=client_parent['parent'].id).first_name == 'change'
