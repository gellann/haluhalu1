from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.
class CustomUser(AbstractUser):
    #so no need na magdagdag ng username and email since nasa AbstractUser na mga yon
    profile_pic = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    is_seller = models.BooleanField(default=False)

    def __str__(self):
        return self.username
