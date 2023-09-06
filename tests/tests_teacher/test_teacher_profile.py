import pytest
from accounts.models import User
from teacher.models import Employee


@pytest.mark.django_db
def test_teacher_update_access_1(client_conf, client_parent, client_director):
    response = client_director['client'].post('/add/teacher/', {
        'email': 'tests_add@gmail.com',
        'role': 2,
        'salary': 20,
        'group': client_director['group'].id
    })
    teacher = Employee.objects.get(user__email='tests_add@gmail.com')
    response = client_conf.get(f"/employee/profile/{teacher.id}/")
    assert response.status_code == 302
    response_parent = client_parent['client'].get(f"/employee/profile/{teacher.id}/")
    assert response_parent.status_code == 403
    response = client_director['client'].get(f"/employee/profile/{teacher.id}/")
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/employee/profile/{teacher.id}/")
    assert response_parent.status_code == 302


@pytest.mark.django_db
def test_teacher_update_access_2(client_director, client_parent):
    response = client_director['client'].post('/add/teacher/', {
        'email': 'tests_add@gmail.com',
        'role': 2,
        'salary': 20,
        'group': client_director['group'].id
    })
    teacher = Employee.objects.get(user__email='tests_add@gmail.com')
    assert Employee.objects.filter(user__email='tests_add@gmail.com').first()
    user = User.objects.get(id=teacher.user.id)
    assert user.get_user_permissions() == {'teacher.is_teacher'}
    assert user.email == teacher.user.email
    client_parent['client'].logout()
    client_parent['client'].force_login(user=teacher.user)
    response_teacher = client_parent['client'].get(f"/employee/profile/{teacher.id}/")
    assert response_teacher.status_code == 200
    response = client_director['client'].get(f"/employee/profile/{teacher.id}/")
    assert response.status_code == 200
