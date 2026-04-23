from rest_framework import serializers
from .models import Reservation

class ReservationSerializer(serializers.ModelSerializer):

  #remove all constraints on this field, let the database handle it
  seat_code = serializers.CharField(max_length=10, validators=[])
  class Meta:
    model = Reservation
    fields = '__all__'