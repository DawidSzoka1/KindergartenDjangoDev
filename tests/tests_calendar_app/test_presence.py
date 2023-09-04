from datetime import timedelta
from django.utils import timezone
import pytest
from children.models import PresenceModel, Kid
from director.models import Director


@pytest.mark.django_db
def test_presence(client_conf, client_director):
    response = client_conf.get(f"/presence/calendar/")
    assert response.status_code == 302
    response_post = client_conf.post(f"/presence/calendar/",
                                     {'data': f"{client_director['kid'].id}2"})
    assert response_post.status_code == 302
    assert not PresenceModel.objects.filter(kid=client_director['kid'])


@pytest.mark.django_db
def test_presence_2(client_director):
    client_director['client'].logout()
    client_director['client'].force_login(user=client_director['user'])
    response = client_director['client'].get(f"/presence/calendar/")
    assert response.status_code == 200
    response_post = client_director['client'].post(f"/presence/calendar/",
                                                   {'data': f"{client_director['kid'].id}2"})
    assert response_post.status_code == 302
    assert PresenceModel.objects.filter(kid=client_director['kid'])


@pytest.mark.django_db
def test_presence_parent(client_parent):
    response = client_parent['client'].get(f"/presence/calendar/")
    assert response.status_code == 200
    response = client_parent['client'].post(f"/presence/calendar/",
                                            {'data': f"{client_parent['kid'].id}3"})
    assert response.status_code == 302
    assert PresenceModel.objects.get(kid=client_parent['kid'])
    assert PresenceModel.objects.get(kid=client_parent['kid']).get_presenceType_display() == 'Planowana nieobecnosc'
    assert PresenceModel.objects.get(kid=client_parent['kid']).day.strftime("%Y-%m-%d") == (
            timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")


@pytest.mark.django_db
def test_presence_parent_2(client_parent, client_director):
    response = client_parent['client'].post(f"/presence/calendar/",
                                            {'data': f"{client_director['kid'].id}3"})
    assert response.status_code == 302
    assert not PresenceModel.objects.filter(kid=client_director['kid'].id)
