import pytest


def test_parent_access_1(client_conf):
    response = client_conf.get('/list/parents/')
    assert response.status_code == 302


@pytest.mark.django_db
def test_parent_access_2(client_director, client_parent):
    response = client_director['client'].get('/list/parents/')
    assert response.status_code == 200
    response_parent = client_parent['client'].get('/list/parents/')
    assert response_parent.status_code == 403
