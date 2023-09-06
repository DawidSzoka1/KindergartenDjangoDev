import pytest

from payments_plans.models import PaymentPlan


@pytest.mark.django_db
def test_payment_delete_get(client_conf, client_parent, client_director):
    response = client_conf.get(f"/delete/payments/plans/{client_director['payment'].id}/")
    assert response.status_code == 302
    response_parent = client_parent['client'].get(f"/delete/payments/plans/{client_director['payment'].id}/")
    assert response_parent.status_code == 403
    response = client_director['client'].get(f"/delete/payments/plans/{client_director['payment'].id}/")
    assert response.status_code == 403
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/delete/payments/plans/{client_director['payment'].id}/")
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_payment_delete_post(client_director, client_parent):
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].post(f"/delete/payments/plans/{client_director['payment'].id}/")
    assert response_parent.status_code == 403
    assert PaymentPlan.objects.filter(id=client_director['payment'].id).first()
    response = client_director['client'].post(f"/delete/payments/plans/{client_director['payment'].id}/")
    assert response.status_code == 302
    assert not PaymentPlan.objects.filter(id=client_director['payment'].id).first()


