import pytest
from accounts.models import User


@pytest.mark.django_db
def test_register_get(client_conf, client_parent, client_director):
    response = client_conf.get('/register/')
    assert response.status_code == 200
    response_parent = client_parent['client'].get('/register/')
    assert response_parent.status_code == 302
    response = client_director['client'].get('/register/')
    assert response.status_code == 302
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_parent = client_parent['client'].get('/register/')
    assert response_parent.status_code == 302


@pytest.mark.django_db
def test_register_post(client_conf):
    response = client_conf.post('/register/', {
        'email': 'email@gmail.com',
        'password1': 'Hasło1234567',
        'password2': 'Hasło1234567'
    })
    assert response.status_code == 302
    assert User.objects.get(email='email@gmail.com')
    assert User.objects.get(email='email@gmail.com').get_user_permissions() == {'director.is_director'}
