from django.db import models

# Create your models here.


class OAuth2AppRateLimit(models.Model):
    client_id = models.CharField(max_length=255, unique=True)
    rate = models.CharField(max_length=30, default='5/h')

    def __str__(self):
        return f'{self.rate}'
