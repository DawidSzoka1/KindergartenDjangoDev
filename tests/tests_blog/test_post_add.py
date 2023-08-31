import pytest

from blog.models import Post


@pytest.mark.django_db
def test_post_add_access(client_conf, client_director):
    response = client_conf.post('/wydarzenia/', {
        'author': client_director['user'].id,
        'director': client_director['director'].id,
        'is_active': True,
        'group': client_director['group'].id,
        'content': 'testpy'
    })
    assert response.status_code == 302
    assert len(Post.objects.filter(director=client_director['director']).filter(content='testpy')) == 0


@pytest.mark.django_db
def test_post_add(client_director):
    response = client_director['client'].post('/wydarzenia/', {
        'author': client_director['user'].id,
        'director': client_director['director'].id,
        'is_active': True,
        'group': client_director['group'].id,
        'content': 'testpy'
    })
    assert response.status_code == 302
    assert len(Post.objects.filter(director=client_director['director'])) > 0
