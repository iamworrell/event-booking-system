from django.db import models

class Event(models.Model):
  event_id = models.AutoField(primary_key=True)
  event_name = models.CharField(max_length=100)
  venue = models.CharField(max_length=100)
  total_seats = models.IntegerField()
  start_time = models.DateTimeField()
  end_time = models.DateTimeField()
  class Meta:
    #specify table in database
    db_table = 'events'
    #tell django you already have a table and database
    managed = False