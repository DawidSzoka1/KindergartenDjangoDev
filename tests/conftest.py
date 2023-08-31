from django.test import Client
import pytest
from accounts.models import User
from blog.models import Post
from children.models import Kid
from groups.models import Groups
from director.models import Director
from payments_plans.models import PaymentPlan
from meals.models import Meals


@pytest.fixture
def client_conf():
    client = Client()
    return client


@pytest.fixture
def client_director():
    client = Client()
    user = User.objects.create(email='test_pytest_director_3@gmail.com', password='password')
    director = Director.objects.get(user__email='test_pytest_director_3@gmail.com')
    group = Groups.objects.create(name='pytest', capacity=3, principal=director)
    meal = Meals.objects.create(name='py', per_day=3, principal=director)
    payment = PaymentPlan.objects.create(name='t', principal=director)
    kid = Kid.objects.create(first_name='l', last_name='s', principal=director, start='2023-09-26')
    post = Post.objects.create(author=user, director=director, content='test', is_active=True)
    post.group.add(group)
    client.force_login(user=user)
    context = {'client': client, 'director': director, 'group': group, 'meal': meal, 'user': user, 'payment': payment,
               'kid': kid, 'post': post}

    return context
