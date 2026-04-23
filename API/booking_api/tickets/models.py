from django.db import models
from users.models import Users
from events.models import Event
from reservations.models import Reservation

class Ticket(models.Model):
  id = models.AutoField(primary_key=True, db_column='ticket_id')
  price = models.IntegerField()
  #on_delete=models.CASCADE
  #if the parent is deleted then all children are removed
  
  user_id = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
  event_id = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='event_id')
  seat_code = models.CharField(max_length=10)
  
  class Meta:
    db_table = 'tickets'
    managed = False
    constraints = [
        models.UniqueConstraint(
            fields=['event_id', 'seat_code'],
            name='unique_event_seat'
        )
    ]