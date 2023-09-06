import pytest


@pytest.mark.django_db
def test_payments_access_1(client_conf, client_parent):
    response = client_conf.get('/list/payments/plans/')
    assert response.status_code == 302
    response_parent = client_parent['client'].get('/list/payments/plans/')
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_payments_access_2(client_director, client_parent):
    response = client_director['client'].get('/list/payments/plans/')
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get('/list/payments/plans/')
    assert response_parent.status_code == 200
    assert response_parent.content != response.content
