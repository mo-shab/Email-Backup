from django.db import models
from django.contrib.auth.models import User

class EmailConfiguration(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_address = models.EmailField()
    imap_server = models.CharField(max_length=255)
    smtp_server = models.CharField(max_length=255)
    email_password = models.CharField(max_length=255)
    port_imap = models.IntegerField(default=993)
    port_smtp = models.IntegerField(default=587)

    def __str__(self):
        return f'{self.user.username} - Email Configuration'