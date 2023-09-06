import pytest

from payments_plans.models import PaymentPlan


@pytest.mark.django_db
def test_payment_add_get(client_conf, client_parent, client_director):
    response = client_conf.get('/add/payments/plans/')
    assert response.status_code == 302
    response_parent = client_parent['client'].get('/add/payments/plans/')
    assert response_parent.status_code == 403
    response = client_director['client'].get('/add/payments/plans/')
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get('/add/payments/plans/')
    assert response_parent.status_code == 200
    assert response_parent.content != response.content


@pytest.mark.django_db
def test_payment_add_post(client_director):
    response = client_director['client'].post('/add/payments/plans/', {
        'principal': client_director['director'].id,
        'is_active': True,
        'name': 'name',
        'price': 20
    })
    assert response.status_code == 302
    assert PaymentPlan.objects.get(name='name').principal == client_director['director']
