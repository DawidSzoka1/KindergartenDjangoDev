from django.db import models
from accounts.models import User
from director.models import Director
from children.models import Groups
# Create your models here.


class Post(models.Model):
    CATEGORY_CHOICES = (
        ('holiday', 'Święto / Wolne'),
        ('trip', 'Wycieczka'),
        ('meeting', 'Spotkanie'),
        ('performance', 'Występ / Teatrzyk'),
        ('info', 'Ogólne'),
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    date_posted = models.DateTimeField(auto_now_add=True, null=True)
    # Kiedy wydarzenie faktycznie się odbywa
    event_date = models.DateField(null=True, blank=True)
    content = models.TextField()
    title = models.CharField(max_length=200, default="Ogłoszenie") # Dodajemy tytuł
    group = models.ManyToManyField(Groups)
    director = models.ForeignKey(Director, on_delete=models.CASCADE, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='info')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


