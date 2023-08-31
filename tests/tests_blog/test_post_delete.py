import pytest

from blog.models import Post


@pytest.mark.django_db
def test_post_delete(client_conf, client_director):
    response = client_conf.post(f"/wydarzenia/usun/{client_director['post'].id}/")
    assert response.status_code == 302
    assert Post.objects.get(id=client_director['post'].id).is_active


@pytest.mark.django_db
def test_post_delete_2(client_director):
    response = client_director['client'].post(f"/wydarzenia/usun/{1}/")
    assert response.status_code == 404
    response = client_director['client'].post(f"/wydarzenia/usun/{client_director['post'].id}/")
    assert response.status_code == 302
    assert not Post.objects.get(id=client_director['post'].id).is_active


