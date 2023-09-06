import pytest
from accounts.models import User
from teacher.models import Employee


@pytest.mark.django_db
def test_teacher_update_get(client_conf, client_parent, client_director):
    response = client_director['client'].post('/add/teacher/', {
        'email': 'tests_add@gmail.com',
        'role': 2,
        'salary': 20,
        'group': client_director['group'].id
    })
    teacher = Employee.objects.get(user__email='tests_add@gmail.com')
    response = client_conf.get(f"/teacher/update/{teacher.id}/")
    assert response.status_code == 302
    response_parent = client_parent['client'].get(f"/teacher/update/{teacher.id}/")
    assert response_parent.status_code == 403
    response = client_director['client'].get(f"/teacher/update/{teacher.id}/")
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get(f"/teacher/update/{teacher.id}/")
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_teacher_update_post(client_director, client_parent):
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
    response_teacher = client_parent['client'].post(f"/teacher/update/{teacher.id}/", {
        'principal': teacher.principal.first().id,
        'role': 2,
        'user': teacher.user.id,
        'salary': 5433,
        'group': teacher.group.id,
        'first_name': 'name',
        'last_name': 'last',
        'gender': 2,
        'city': 'miasto',
        'address': 'address',
        'zip_code': '15-606',
        'phone': '+48234234234'
    })
    assert response_teacher.status_code == 302
    assert Employee.objects.get(id=teacher.id).first_name == 'name'
    response = client_director['client'].post(f"/teacher/update/{teacher.id}/", {
        'role': 2,
        'salary': 5433,
        'group': client_director['group'].id
    })
    assert response.status_code == 302
    assert Employee.objects.get(user__email='tests_add@gmail.com').salary == 5433
