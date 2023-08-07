from django.db import models
from accounts.models import User
from director.models import Director
from children.models import Groups
from PIL import Image
from django.utils import timezone
from django.urls import reverse

# Create your models here.


class Post(models.Model):
    title = models.CharField(max_length=128)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(null=True, upload_to='events_foto')
    date_posted = models.DateTimeField(default=timezone.now)
    content = models.TextField()
    group = models.ManyToManyField(Groups)
    director = models.ManyToManyField(Director)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)

            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail_view', kwargs={'pk': self.pk})
