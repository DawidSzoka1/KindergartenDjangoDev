import pytest

from payments_plans.models import PaymentPlan


@pytest.mark.django_db
def test_payment_update_get(client_conf, client_parent, client_director):
    response = client_conf.get(f"/update/payments/plans/{client_director['payment'].id}/")
    assert response.status_code == 302
    response_parent = client_parent['client'].get(f"/update/payments/plans/{client_director['payment'].id}/")
    assert response_parent.status_code == 403
    response = client_director['client'].get(f"/update/payments/plans/{client_director['payment'].id}/")
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/update/payments/plans/{client_director['payment'].id}/")
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_payment_update_post(client_director):
    assert client_director['payment'].name == 't'
    response = client_director['client'].post(f"/update/payments/plans/{client_director['payment'].id}/", {
        'principal': client_director['director'].id,
        'is_active': True,
        'name': 'change',
        'price': 20
    })
    assert response.status_code == 302
    assert PaymentPlan.objects.get(name='change').principal == client_director['director']
    assert PaymentPlan.objects.get(name='change') == client_director['payment']
