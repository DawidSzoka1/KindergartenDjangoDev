import pytest


@pytest.mark.django_db
def test_parent_search_access(client_conf, client_director):
    response = client_conf.get('/parent/search/')
    assert response.status_code == 302
    response_logged = client_director['client'].get('/parent/search/')
    assert response_logged.status_code == 302
    assert response.url != response_logged.url


@pytest.mark.django_db
def test_parent_search(client_parent):
    client_parent['client'].logout()
    client_parent['client'].force_login(user=client_parent['director'].user)
    response_logged = client_parent['client'].post('/parent/search/',
                                                   {'search': client_parent['parent'].user.email})
    assert client_parent['parent'] in response_logged.context['page_obj']
