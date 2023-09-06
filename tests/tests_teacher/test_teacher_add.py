import pytest

from payments_plans.models import PaymentPlan
from teacher.models import Employee


@pytest.mark.django_db
def test_teacher_add_get(client_conf, client_parent, client_director):
    response = client_conf.get('/add/teacher/')
    assert response.status_code == 302
    response_parent = client_parent['client'].get('/add/teacher/')
    assert response_parent.status_code == 403
    response = client_director['client'].get('/add/teacher/')
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get('/add/teacher/')
    assert response_parent.status_code == 200
    assert response_parent.content != response.content


@pytest.mark.django_db
def test_teacher_add_post(client_director):
    assert not Employee.objects.filter(user__email='tests_add@gmail.com').first()
    response = client_director['client'].post('/add/teacher/', {
        'email': 'tests_add@gmail.com',
        'role': 2,
        'salary': 20,
        'group': client_director['group'].id
    })
    assert response.status_code == 302
    assert Employee.objects.get(user__email='tests_add@gmail.com')
