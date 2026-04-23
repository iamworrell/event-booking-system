#Django Function Based
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import Event
from .serializers import EventSerializer

#transaction.atomic() treats all database operations inside it as a single unit
#if anything fails, ALL changes are rolled back; nothing is partially saved

#LIST & CREATE
#Handles /api/events/

@api_view(['GET', 'POST'])
def event_list(request):

    #GET return all events
    if request.method == 'GET':
        events = Event.objects.all()
        # many=True tells the serializer to handle a list of objects
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #POST create a new event
    elif request.method == 'POST':
        try:
            with transaction.atomic():
                # pass incoming data to the serializer for validation
                serializer = EventSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                # serializer found validation errors; return them
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


#RETRIEVE, UPDATE, DELETE
#Handles /api/events/<id>/

@api_view(['GET', 'PUT', 'DELETE'])
def event_detail(request, pk):

    # try to find the event
    # return 404 if it doesn't exist
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

    #GET
    #return a single event
    if request.method == 'GET':
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)

    #PUT
    #update an existing event
    elif request.method == 'PUT':
        try:
            with transaction.atomic():
                # partial=False means all fields must be provided
                serializer = EventSerializer(event, data=request.data, partial=False)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data, status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    #DELETE
    #remove an event
    elif request.method == 'DELETE':
        try:
            with transaction.atomic():
                event.delete()
                return Response({'message': 'Event deleted'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#Only Django Rest Framework - transaction.atomic() to roll back errors
# from rest_framework import viewsets, status
# from rest_framework.response import Response
# from .models import Event
# from .serializers import EventSerializer

# class EventViewSet(viewsets.ModelViewSet):
#     queryset = Event.objects.all()
#     serializer_class = EventSerializer