from django.db import models

class Users(models.Model):
  user_id = models.AutoField(primary_key=True)
  date_of_birth = models.DateField()
  first_name = models.CharField(max_length=100)
  last_name = models.CharField(max_length=100)

  class Meta:
    db_table = 'users'
    managed = False