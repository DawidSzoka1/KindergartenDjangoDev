import pytest


@pytest.mark.django_db
def test_teachers_access_1(client_conf, client_parent):
    response = client_conf.get('/list/teachers/')
    assert response.status_code == 302
    response_parent = client_parent['client'].get('/list/teachers/')
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_teachers_access_2(client_director, client_parent):
    response = client_director['client'].get('/list/teachers/')
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get('/list/teachers/')
    assert response_parent.status_code == 200
    assert response_parent.content != response.content
