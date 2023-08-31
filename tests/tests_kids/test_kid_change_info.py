import pytest

from children.models import Kid


@pytest.mark.django_db
def test_change_info_access(client_director):
    response = client_director['client'].get(f"/change/kid/info/{client_director['kid'].id}/")
    assert response.status_code == 200
    response = client_director['client'].get(f"/change/kid/info/4/")
    assert response.status_code == 404
    client_director['client'].logout()
    response = client_director['client'].get(f"/change/kid/info/{client_director['kid'].id}/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_change_info(client_director):
    response = client_director['client'].post(f"/change/kid/info/{client_director['kid'].id}/",
                                              {'first_name': 'change', 'last_name': 'test',
                                               'group': client_director['group'].id, 'gender': 1,
                                               'start': '2023-09-26', 'payment_plan': client_director['payment'].id,
                                               'kid_meals': client_director['meal'].id,
                                               'principal': client_director['director'].id,
                                               'date_of_birth': '2023-09-26'
                                               })
    assert response.status_code == 302
    assert len(Kid.objects.filter(principal=client_director['director']).filter(first_name='change')) > 0

