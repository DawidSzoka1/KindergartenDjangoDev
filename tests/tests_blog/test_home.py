import pytest



def test_home(client_conf):
    response = client_conf.get('')
    assert response.status_code == 200


@pytest.mark.django_db
def test_home_user(client_director):
    response = client_director['client'].get('')
    assert response.status_code == 200
    client_director['client'].logout()
    response_logout = client_director['client'].get('')
    assert response.content != response_logout.content



