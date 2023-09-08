import os
import shutil
from io import BytesIO
import pytest
from director.models import GroupPhotos
from groups.models import Groups


@pytest.mark.django_db
def test_group_update_access_get(client_director, client_parent, client_conf):
    response = client_director['client'].get(f"/update/group/info/{client_director['group'].id}/")
    assert response.status_code == 200
    response_parent = client_parent['client'].get(f"/update/group/info/{client_director['group'].id}/")
    assert response_parent.status_code == 403
    response = client_conf.get(f"/update/group/info/{client_director['group'].id}/")
    assert response.status_code == 302


@pytest.mark.django_db
def test_group_update_access_post(client_director):
    img = BytesIO(

        b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00"

        b"\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x00\x00"
    )

    img.name = "myimage.jpg"

    client_director['client'].post('/photo/add/', {'type': 'group',
                                                   'file': img,
                                                   'name': 'add'
                                                   })
    photo = GroupPhotos.objects.get(name='add')
    response = client_director['client'].post(f"/update/group/info/{client_director['group'].id}/",
                                              {'name': 'change', 'capacity': 30, 'yearbook': 2000, 'photo': photo.id,
                                               'is_active': True, 'principal': client_director['director'].id})
    assert response.status_code == 302
    assert Groups.objects.get(id=client_director['group'].id).name == 'change'

    photo.group_photos.delete(save=True)
    parent = '/home/dawid/django/MarchewkaDjango/media'
    director = f"director_{client_director['director'].id}"
    path = os.path.join(parent, director)
    shutil.rmtree(path)
