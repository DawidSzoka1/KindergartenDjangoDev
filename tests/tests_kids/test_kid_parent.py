import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
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
    client_director['client'].logout()
    client_director['client'].force_login(user=user)
    content_type = ContentType.objects.get_for_model(ParentA)
    permission = Permission.objects.get(content_type=content_type, codename='is_parent')
    parent.principal.add(client_director['director'])
    parent.user.user_permissions.clear()
    parent.user.user_permissions.add(permission)
    user.parenta.save()
    response = client_director['client'].get(f"/kid/parent/info/{client_director['kid'].id}/")
    assert response.status_code == 200
