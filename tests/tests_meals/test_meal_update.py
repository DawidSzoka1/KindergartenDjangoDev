import os
import shutil
from io import BytesIO
import pytest
from director.models import MealPhotos
from meals.models import Meals


@pytest.mark.django_db
def test_meal_update_access_get(client_conf, client_parent, client_director):
    response = client_conf.get(f"/meals/update/{client_director['meal'].id}/")
    assert response.status_code == 302
    response_dir = client_director['client'].get(f"/meals/update/{client_director['meal'].id}/")
    assert response_dir.status_code == 200
    response_parent = client_parent['client'].get(f"/meals/update/{client_director['meal'].id}/")
    assert response_parent.status_code == 403


@pytest.mark.django_db
def test_meal_update_access_post(client_director):
    img = BytesIO(

        b"GIF89a\x01\x00\x01\x00\x00\x00\x00!\xf9\x04\x01\x00\x00\x00"

        b"\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x01\x00\x00"
    )

    img.name = "myimage.jpg"

    client_director['client'].post('/photo/add/', {'type': 'meal',
                                                   'file': img,
                                                   'name': 'add'
                                                   })
    photo = MealPhotos.objects.get(name='add')
    response = client_director['client'].post(f"/meals/update/{client_director['meal'].id}/", {'name': 'change', 'description': 'opis', 'per_day': 20,
                                                             'photo': photo.id})
    assert response.status_code == 302
    assert Meals.objects.get(name='change')
    assert Meals.objects.get(id=client_director['meal'].id).name == 'change'
    photo.meal_photos.delete(save=True)
    parent = '/home/dawid/django/MarchewkaDjango/media'
    director = f"director_{client_director['director'].id}"
    path = os.path.join(parent, director)
    shutil.rmtree(path)
