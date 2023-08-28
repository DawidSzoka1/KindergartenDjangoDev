from django.db import models
from accounts.models import User
from director.models import Director
from children.models import Groups
# Create your models here.


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True, null=True)
    content = models.TextField()
    group = models.ManyToManyField(Groups)
    director = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.content


