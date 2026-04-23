#Django Rest Framework Function Based
import json
from django.http import JsonResponse
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from tickets.models import Ticket
from .models import Reservation
from .serializers import ReservationSerializer


#LIST & CREATE
#Handles /api/reservations/


class ReservationListView(View):
  #POST
  #create a new reservation
  def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        #Manual validation
        required_fields = ['expires_at', 'user_id', 'event_id', 'seat_code']
        missing = [f for f in required_fields if f not in data]
        if missing:
          return JsonResponse({'error': f'Missing fields: {missing}'}, status=400)

        try:
          # transaction.atomic() treats all database operations inside it as a single unit
          # if anything fails, ALL changes are rolled back — nothing is partially saved
          with transaction.atomic():
            # 1. Check if tickets table already contains the seat_code for the event (if it does no reserving)
            if Ticket.objects.filter(
                seat_code=data['seat_code'],
                event_id_id=data['event_id'],
              ).exists():
              print("Seat has already been selected")
              return JsonResponse({'error': 'Seat Not Available'}, status=400)
                  
            # 2. Create the reservation if ticket doesnt exist
            reservation = Reservation.objects.create(
                user_id_id=data['user_id'],
                event_id_id=data['event_id'],
                seat_code=data['seat_code'],
            )
            print("Reservation has been created")
            return JsonResponse({'seat_code': reservation.seat_code, 'message': 'Reservation created'}, status=201)
        except Exception as e:
          print('Hellp')
          print("ERRORS:", e)
          return JsonResponse({'error': str(e)})
        
@api_view(['GET', 'POST'])
def reservation_list(request):
    #GET
    #return all reservations
    if request.method == 'GET':
        reservations = Reservation.objects.all()
        # many=True tells the serializer to handle a list of objects
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
    # elif request.method == 'POST':
    #     try:
    #         # transaction.atomic() treats all database operations inside it as a single unit
    #         # if anything fails, ALL changes are rolled back — nothing is partially saved
    #         with transaction.atomic():
    #             serializer = ReservationSerializer(data=request.data)
    #             if serializer.is_valid():
    #                 serializer.save()
    #                 return Response(serializer.data, status=status.HTTP_201_CREATED)
    #             print("SERIALIZER ERRORS:", serializer.errors)
    #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #     except Exception as e:
    #         return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        


#RETRIEVE, UPDATE, DELETE
#Handles /api/reservations/<id>/

@api_view(['GET', 'PUT', 'DELETE'])
def reservation_detail(request, pk):

    #try to find the reservation
    #return 404 if it doesn't exist
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response({'error': 'Reservation not found'}, status=status.HTTP_404_NOT_FOUND)

    #GET
    #return a single reservation
    if request.method == 'GET':
        serializer = ReservationSerializer(reservation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #PUT
    #update an existing reservation
    elif request.method == 'PUT':
        try:
            # transaction.atomic() treats all database operations inside it as a single unit
            # if anything fails, ALL changes are rolled back; nothing is partially saved
            with transaction.atomic():
                serializer = ReservationSerializer(reservation, data=request.data, partial=False)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #DELETE
    #remove a reservation
    elif request.method == 'DELETE':
        try:
            # transaction.atomic() treats all database operations inside it as a single unit
            # if anything fails, ALL changes are rolled back; nothing is partially saved
            with transaction.atomic():
                reservation.delete()
                return Response({'message': 'Reservation deleted'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



# from rest_framework import viewsets
# from .models import Reservation
# from .serializers import ReservationSerializer

# #Only Django Rest Framework
# class ReservationViewSet(viewsets.ModelViewSet):
#     queryset = Reservation.objects.all()
#     serializer_class = ReservationSerializer