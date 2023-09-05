from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client
import pytest
from accounts.models import User
from blog.models import Post
from children.models import Kid
from groups.models import Groups
from director.models import Director
from parent.models import ParentA
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


@pytest.fixture
def client_parent():
    client = Client()
    dir_user = User.objects.create(email='test_pytest_director_4@gmail.com', password='password')
    director = Director.objects.get(user__email='test_pytest_director_4@gmail.com')
    user = User.objects.create(email='panret@gmail.com', password='password')
    parent = ParentA.objects.create(user=user)
    group = Groups.objects.create(name='pytest', capacity=3, principal=director)
    kid = Kid.objects.create(first_name='l', last_name='s', principal=director, group=group, start='2023-09-26')
    parent.kids.add(kid)
    content_type = ContentType.objects.get_for_model(ParentA)
    permission = Permission.objects.get(content_type=content_type, codename='is_parent')
    parent.principal.add(director)
    parent.user.user_permissions.clear()
    parent.user.user_permissions.add(permission)
    user.parenta.save()
    client.force_login(user=user)
    context = {'client': client, 'director': director, 'kid': kid, 'group': group, 'parent': parent}
    return context
