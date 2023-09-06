import pytest
from django.contrib.auth.hashers import check_password

from accounts.models import User


@pytest.mark.django_db
def test_change_password_get(client_conf, client_parent, client_director):
    response = client_conf.get('/profile/password/update/')
    assert response.status_code == 302
    response_parent = client_parent['client'].get('/profile/password/update/')
    assert response_parent.status_code == 200
    response = client_director['client'].get('/profile/password/update/')
    assert response.status_code == 200
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get('/profile/password/update/')
    assert response_parent.status_code == 200


@pytest.mark.django_db
def test_change_password_post(client_director):
    response = client_director['client'].post('/profile/password/update/', {
        'old_password': 'password123',
        'new_password1': 'qweasd321',
        'new_password2': 'qweasd321'
    })
    user = User.objects.get(id=client_director['user'].id)
    assert response.status_code == 302
    assert user.email == 'test_pytest_director_3@gmail.com'
    assert user.check_password('qweasd321')

