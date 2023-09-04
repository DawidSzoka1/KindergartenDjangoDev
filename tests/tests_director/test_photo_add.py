import pytest
from io import BytesIO
from director.models import GroupPhotos
import os
import shutil


@pytest.mark.django_db
def test_photo_add_access(client_director, client_conf, client_parent):
    response = client_director['client'].get('/photo/add/')
    assert response.status_code == 200
    response = client_conf.get('/photo/add/')
    assert response.status_code == 302
    response = client_parent['client'].get('/photo/add/')
    assert response.status_code == 403


@pytest.mark.django_db
def test_photo_add_access_post(client_director):
    img = BytesIO(

        b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00"

        b"\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x00\x00"
    )

    img.name = "myimage.jpg"

    response = client_director['client'].post('/photo/add/', {'type': 'group',
                                                              'file': img,
                                                              'name': 'add'
                                                              })
    assert response.status_code == 302
    assert GroupPhotos.objects.get(name='add')
    GroupPhotos.objects.get(name='add').group_photos.delete(save=True)
    parent = '/home/dawid/django/MarchewkaDjango/media'
    director = f"director_{client_director['director'].id}"
    path = os.path.join(parent, director)
    shutil.rmtree(path)
