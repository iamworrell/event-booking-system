from django.db import models
from users.models import Users
from events.models import Event

class Reservation(models.Model):
    # tell django to treat the unique constraint as its internal PK
    # pick seat_code since it is already part of your unique constraint
    # Django needs a primary key
    seat_code = models.CharField(max_length=10, primary_key=True)
    user_id = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    event_id = models.ForeignKey(Event, on_delete=models.CASCADE, db_column='event_id')
    expires_at = models.DateTimeField()
    
    class Meta:
      db_table = 'seat_reservation'
      managed = False
      constraints = [
          models.UniqueConstraint(
              fields=['event_id', 'seat_code'],
              name='unique_seat_hold'
          )
      ]