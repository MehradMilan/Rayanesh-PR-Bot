from django.db import models

# Create your models here.
class Bot_Command(models.Model):
    JOIN_GROUP_COMMAND = "joing_group"
    AUTHORIZE_COMMAND = "authorize"
    START_COMMAND = 'start'
    
class Raya_Command(models.Model):
    ACCEPT_JOIN_GROUP = "accept_join"