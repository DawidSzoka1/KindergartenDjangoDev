import pytest


@pytest.mark.django_db
def test_groups_access(client_director, client_parent):
    response = client_director['client'].get('/list/groups/')
    assert response.status_code == 200
    response_parent = client_parent['client'].get('/list/groups/')
    assert response_parent.status_code == 200
    assert response.content != response_parent.content


@pytest.mark.django_db
def test_groups_access_2(client_conf):
    response = client_conf.get('/list/groups/')
    assert response.status_code == 302
