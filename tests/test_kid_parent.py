import pytest

from accounts.models import User
from children.models import Kid
from parent.models import ParentA


@pytest.mark.django_db
def test_kid_parent_access(client_director):
    response = client_director['client'].get(f"/kid/parent/info/{client_director['kid'].id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_kid_parent_access(client_director):
    user = User.objects.create(email='panret@gmail.com', password='password')
    parent = ParentA.objects.create(user=user)
    parent.kids.add(client_director['kid'])
    response = client_director['client'].get(f"/kid/parent/info/{client_director['kid'].id}/")
    assert response.status_code == 200
