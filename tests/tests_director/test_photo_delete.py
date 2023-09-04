import pytest
from io import BytesIO
from director.models import GroupPhotos
from PIL import Image


@pytest.mark.django_db
def test_photo_delete_access(client_director, client_conf, client_parent):
    img = BytesIO(

        b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00"

        b"\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x00\x00"
    )

    img.name = "myimage.jpg"

    response = client_director['client'].post('/photo/add/', {'type': 'group',
                                                              'file': img,
                                                              'name': 'to_delete'
                                                              })
    photo = GroupPhotos.objects.get(name='to_delete')
    response = client_director['client'].get(f'/photo/delete/{photo.id}/')
    assert response.status_code == 403
    response = client_conf.get(f'/photo/delete/{photo.id}/')
    assert response.status_code == 302
    response = client_parent['client'].get(f'/photo/delete/{photo.id}/')
    assert response.status_code == 403
    photo.group_photos.delete(save=True)


@pytest.mark.django_db
def test_photo_delete_access_post(client_director, client_parent):
    img = BytesIO(

        b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00"

        b"\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x00\x00"
    )

    img.name = "myimage.jpg"

    response = client_director['client'].post('/photo/add/', {'type': 'group',
                                                              'file': img,
                                                              'name': 'to_delete'
                                                              })
    photo = GroupPhotos.objects.get(name='to_delete')
    response = client_parent['client'].post(f'/photo/delete/{photo.id}/', {'delete': '1'})
    assert response.status_code == 403
    assert GroupPhotos.objects.get(name='to_delete').is_active
    response = client_director['client'].post(f'/photo/delete/{photo.id}/', {'delete': '1'})
    assert response.status_code == 302
    assert not GroupPhotos.objects.get(name='to_delete').is_active

    photo.group_photos.delete(save=True)

