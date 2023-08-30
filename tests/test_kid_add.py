import pytest
from children.models import Kid



@pytest.mark.django_db
def test_get_add(client_director):
    response = client_director['client'].get('/add/kid/')
    assert response.status_code == 200
    client_director['client'].logout()
    response = client_director['client'].get('/add/kid/')
    assert response.status_code == 404


@pytest.mark.django_db
def test_post_add(client_director):
    response_add = client_director['client'].post('/add/kid/',
                                                  {'first_name': 'test', 'last_name': 'test',
                                                   'group': client_director['group'].id, 'gender': 1,
                                                   'start': '2023-09-26', 'payment_plan': client_director['payment'].id,
                                                   'kid_meals': client_director['meal'].id,
                                                   'principal': client_director['director'].id,
                                                   'date_of_birth': '2023-09-26'
                                                   })
    assert response_add.status_code == 302
    assert len(Kid.objects.filter(is_active=True).filter(principal=client_director['director'].id).filter(
        first_name='test')) > 0
