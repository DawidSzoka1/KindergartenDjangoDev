import pytest


@pytest.mark.django_db
def test_post_search_access(client_conf, client_director):
    response = client_conf.get('/wydarzenia/wyszukane/')
    assert response.status_code == 302
    response_logged = client_director['client'].get('/wydarzenia/wyszukane/')
    assert response_logged.status_code == 302
    assert response.url != response_logged.url


@pytest.mark.django_db
def test_post_search(client_director):
    response_logged = client_director['client'].post('/wydarzenia/wyszukane/',
                                                    {'search': client_director['post'].content})
    assert client_director['post'] in response_logged.context['page_obj']
