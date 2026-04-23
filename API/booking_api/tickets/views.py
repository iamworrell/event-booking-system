#Raw Django - Class Based View
import json
from django.http import JsonResponse
from django.views import View
from django.shortcuts import get_object_or_404
from django.db import transaction

from reservations.models import Reservation
from .models import Ticket
 

class TicketListView(View):

    # GET /api/tickets/ — list all tickets
    def get(self, request):
        tickets = Ticket.objects.all().values(
            'id', 'price', 'user_id', 'event_id', 'seat_code'
        )
        return JsonResponse(list(tickets), safe=False, status=200)

    # POST /api/tickets/ — create a ticket
    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Manual validation
        required_fields = ['price', 'user_id', 'event_id', 'seat_code']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return JsonResponse({'error': f'Missing fields: {missing}'}, status=400)

        
        # 1. Check reservation exists and belongs to this user
        try:
          # transaction.atomic() treats all database operations inside it as a single unit
          # if anything fails, ALL changes are rolled back — nothing is partially saved
          with transaction.atomic():
            #can only get ticket if you have reservation
            reservation = Reservation.objects.get(
                seat_code=data['seat_code'],
                user_id=data['user_id'],
                event_id=data['event_id'],
            )
        except Reservation.DoesNotExist:
            print({'error': 'No valid reservation found for this seat'})
            return JsonResponse({'error': 'No valid reservation found for this seat'}, status=400)
        
        try:
          with transaction.atomic():
            # 2. Create the ticket
            ticket = Ticket.objects.create(
                price=data['price'],
                user_id_id=data['user_id'],
                event_id_id=data['event_id'],
                seat_code=data['seat_code'],
            )

            # 3. Delete the reservation
            reservation.delete()
        except Exception as e:
            print("ERRORS:", e)
            return JsonResponse({'error': str(e)}, status=500)
        return JsonResponse({'id': ticket.id, 'message': 'Ticket created'}, status=201)


class TicketDetailView(View):

    # GET /api/tickets/<id>/ — get one ticket
    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        data = {
            'id': ticket.id,
            'price': ticket.price,
            'user_id': ticket.user_id_id,
            'event_id': ticket.event_id_id,
            'seat_code': ticket.seat_code,
        }
        return JsonResponse(data, status=200)

    # PUT /api/tickets/<id>/ — full update
    def put(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            # transaction.atomic() treats all database operations inside it as a single unit
            # if anything fails, ALL changes are rolled back — nothing is partially saved
            with transaction.atomic():
                ticket.price = data.get('price', ticket.price)
                ticket.user_id = data.get('user_id', ticket.user_id_id)
                ticket.event_id = data.get('event_id', ticket.event_id_id)
                ticket.seat_code = data.get('seat_code', ticket.seat_code)
                ticket.save()
        except Exception as e:
            print("ERRORS:", e)
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'message': 'Ticket updated'}, status=200)

    # DELETE /api/tickets/<id>/ — delete a ticket
    def delete(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        try:
            # transaction.atomic() treats all database operations inside it as a single unit
            # if anything fails, ALL changes are rolled back — nothing is partially saved
            with transaction.atomic():
                ticket.delete()
        except Exception as e:
            print("ERRORS:", e)
            return JsonResponse({'error': str(e)}, status=500)

        return JsonResponse({'message': 'Ticket deleted'}, status=200)
    

# #DJANGO REST FRAMEWORK FUNCTION BASED VERSION
# import json
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from django.db import transaction
# from django.shortcuts import get_object_or_404
# from .models import Ticket

# # @api_view tells DRF which HTTP methods this function accepts
# # request.data automatically parses incoming JSON — no json.loads() needed
# # Response() automatically formats output as JSON — no JsonResponse() needed

# # ─── LIST & CREATE ────────────────────────────────────────────────────────────
# # Handles /api/tickets/

# @api_view(['GET', 'POST'])
# def ticket_list(request):

#     # ── GET: return all tickets ───────────────────────────────────────────────
#     if request.method == 'GET':
#         tickets = Ticket.objects.all().values(
#             'id', 'price', 'user_id', 'event_id', 'seat_code'
#         )
#         # list() converts the queryset into a plain Python list before returning
#         return Response(list(tickets), status=status.HTTP_200_OK)

#     # ── POST: create a new ticket ─────────────────────────────────────────────
#     elif request.method == 'POST':
#         # transaction.atomic() wraps the operation in a database transaction
#         # if anything inside fails, ALL changes are rolled back automatically
#         # nothing is partially saved to the database
#         try:
#             with transaction.atomic():
#                 data = request.data  # DRF parses the JSON body automatically

#                 # Manual validation — check all required fields are present
#                 required_fields = ['price', 'user_id', 'event_id', 'seat_code']
#                 missing = [f for f in required_fields if f not in data]
#                 if missing:
#                     # raising an exception inside atomic() triggers a rollback
#                     raise ValueError(f'Missing fields: {missing}')

#                 # Create the ticket row in the database
#                 ticket = Ticket.objects.create(
#                     price=data['price'],
#                     user_id_id=data['user_id'],       # _id suffix targets the FK column directly
#                     event_id_id=data['event_id'],
#                     seat_code_id=data['seat_code'],
#                 )
#                 return Response(
#                     {'id': ticket.id, 'message': 'Ticket created'},
#                     status=status.HTTP_201_CREATED     # 201 = resource was created
#                 )
#         except ValueError as e:
#             # Catches missing field errors raised above
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             # Catches anything else — DB errors, type errors, etc.
#             # transaction is already rolled back at this point
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# # ─── RETRIEVE, UPDATE, DELETE ─────────────────────────────────────────────────
# # Handles /api/tickets/<id>/

# @api_view(['GET', 'PUT', 'DELETE'])
# def ticket_detail(request, pk):
#     # Try to find the ticket — automatically returns 404 if not found
#     ticket = get_object_or_404(Ticket, pk=pk)

#     # ── GET: return a single ticket ───────────────────────────────────────────
#     if request.method == 'GET':
#         data = {
#             'id': ticket.id,
#             'price': ticket.price,
#             'user_id': ticket.user_id_id,
#             'event_id': ticket.event_id_id,
#             'seat_code': ticket.seat_code_id,
#         }
#         return Response(data, status=status.HTTP_200_OK)

#     # ── PUT: update an existing ticket ────────────────────────────────────────
#     elif request.method == 'PUT':
#         try:
#             with transaction.atomic():
#                 data = request.data  # DRF parses the JSON body automatically

#                 # data.get(field, fallback) — if a field isn't sent, keep the existing value
#                 # this prevents accidentally wiping fields not included in the request
#                 ticket.price = data.get('price', ticket.price)
#                 ticket.user_id_id = data.get('user_id', ticket.user_id_id)
#                 ticket.event_id_id = data.get('event_id', ticket.event_id_id)
#                 ticket.seat_code_id = data.get('seat_code', ticket.seat_code_id)

#                 # .save() writes the updated fields to the database
#                 # without this line the changes only exist in memory
#                 ticket.save()
#                 return Response({'message': 'Ticket updated'}, status=status.HTTP_200_OK)
#         except Exception as e:
#             # Any error here rolls back the update — ticket remains unchanged in DB
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

#     # ── DELETE: remove a ticket ───────────────────────────────────────────────
#     elif request.method == 'DELETE':
#         try:
#             with transaction.atomic():
#                 # .delete() removes the row from the database permanently
#                 ticket.delete()
#                 return Response({'message': 'Ticket deleted'}, status=status.HTTP_200_OK)
#         except Exception as e:
#             # If deletion fails (e.g. DB constraint), rolls back and reports the error
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)