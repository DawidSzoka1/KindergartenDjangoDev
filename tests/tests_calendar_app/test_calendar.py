import pytest

from children.models import PresenceModel


@pytest.mark.django_db
def test_calendar(client_conf, client_director):
    response = client_conf.get(f"/calendar/{client_director['kid'].id}/8/2023/")
    assert response.status_code == 302
    response_post = client_conf.post(f"/calendar/{client_director['kid'].id}/8/2023/",
                                     {'presence': '31 August 2023 1'})
    assert response_post.status_code == 302
    assert not PresenceModel.objects.filter(kid=client_director['kid'])


@pytest.mark.django_db
def test_calendar_logged(client_director):
    response = client_director['client'].get(f"/calendar/{client_director['kid'].id}/8/2023/")
    assert response.status_code == 200
    response = client_director['client'].post(f"/calendar/{client_director['kid'].id}/8/2023/",
                                              {'presence': '31 August 2023 1'})
    assert response.status_code == 302
    assert PresenceModel.objects.get(kid=client_director['kid'])
    assert PresenceModel.objects.get(kid=client_director['kid']).get_presenceType_display() == 'Obecnosc'


@pytest.mark.django_db
def test_calendar_logged_parent(client_parent):
    response = client_parent['client'].get(f"/calendar/{client_parent['kid'].id}/8/2023/")
    assert response.status_code == 200
    response = client_parent['client'].post(f"/calendar/{client_parent['kid'].id}/8/2023/",
                                            {'presence': '1 September 2023 2'})
    assert response.status_code == 302
    assert PresenceModel.objects.get(kid=client_parent['kid'])
    assert PresenceModel.objects.get(kid=client_parent['kid']).get_presenceType_display() == 'Planowana nieobecnosc'
