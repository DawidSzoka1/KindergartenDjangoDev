import pytest
from blog.models import Post


@pytest.mark.django_db
def test_post_change(client_director):
    response = client_director['client'].post(f"/wydarzenia/zmień/{client_director['post'].id}/", {
        'author': client_director['user'].id,
        'director': client_director['director'].id,
        'is_active': True,
        'group': client_director['group'].id,
        'content': 'change'
    })
    assert response.status_code == 302
    assert len(Post.objects.filter(director=client_director['director']).filter(content='test')) == 0
    assert len(Post.objects.filter(director=client_director['director']).filter(content='change')) == 1


@pytest.mark.django_db
def test_post_change_2(client_conf, client_director):
    response = client_conf.post(f"/wydarzenia/zmień/{client_director['post'].id}/", {
        'author': client_director['user'].id,
        'director': client_director['director'].id,
        'is_active': True,
        'group': client_director['group'].id,
        'content': 'change_2'
    })
    assert response.status_code == 302
    assert len(Post.objects.filter(director=client_director['director']).filter(content='test')) == 1
    assert len(Post.objects.filter(director=client_director['director']).filter(content='change_2')) == 0

