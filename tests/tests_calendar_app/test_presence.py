from datetime import timedelta
from django.utils import timezone
from django.test import Client
import pytest
from accounts.models import User
from blog.models import Post
from children.models import Kid
from groups.models import Groups
from director.models import Director
from payments_plans.models import PaymentPlan
from meals.models import Meals
from children.models import PresenceModel


@pytest.mark.django_db
def test_presence(client_conf, client_director):
    response = client_conf.get(f"/presence/calendar/")
    assert response.status_code == 302
    response_post = client_conf.post(f"/presence/calendar/",
                                     {'data': f"{client_director['kid'].id} 2"})
    assert response_post.status_code == 302
    assert not PresenceModel.objects.filter(kid=client_director['kid'])


@pytest.mark.django_db
def test_presence_2():
    client = Client()
    user = User.objects.create(email='test_pytest_director_3@gmail.com')
    user.set_password('password123')
    user.save()
    director = Director.objects.get(user__email='test_pytest_director_3@gmail.com')
    group = Groups.objects.create(name='pytest', capacity=3, principal=director)
    meal = Meals.objects.create(name='py', per_day=3, principal=director)
    payment = PaymentPlan.objects.create(name='t', principal=director, is_active=True)
    kid = Kid.objects.create(first_name='l', last_name='s', principal=director, start='2023-09-26', is_active=True)
    post = Post.objects.create(author=user, director=director, content='test', is_active=True)
    post.group.add(group)
    client.force_login(user=user)

    response = client.get(f"/presence/calendar/")
    assert response.status_code == 200

    response_post = client.post(f"/presence/calendar/",
                                {'data': f"{kid.id} 2"})
    assert response_post.status_code == 302
    assert PresenceModel.objects.filter(kid=kid.id).first().get_presenceType_display() == 'Obecnosc'
    assert PresenceModel.objects.get(kid=kid.id).day.strftime("%Y-%m-%d") == (
        timezone.now()).strftime("%Y-%m-%d")


@pytest.mark.django_db
def test_presence_parent(client_parent):
    response = client_parent['client'].get(f"/presence/calendar/")
    assert response.status_code == 200
    response = client_parent['client'].post(f"/presence/calendar/",
                                            {'data': f"{client_parent['kid'].id} 3"})
    assert response.status_code == 302
    assert PresenceModel.objects.get(kid=client_parent['kid'].id)
    assert PresenceModel.objects.get(kid=client_parent['kid'].id).get_presenceType_display() == 'Planowana nieobecnosc'
    assert PresenceModel.objects.get(kid=client_parent['kid'].id).day.strftime("%Y-%m-%d") == (
            timezone.now() + timedelta(days=1)).strftime("%Y-%m-%d")


@pytest.mark.django_db
def test_presence_parent_2(client_parent, client_director):
    response = client_parent['client'].post(f"/presence/calendar/",
                                            {'data': f"{client_director['kid'].id} 3"})
    assert response.status_code == 302
    assert not PresenceModel.objects.filter(kid=client_director['kid'].id)
