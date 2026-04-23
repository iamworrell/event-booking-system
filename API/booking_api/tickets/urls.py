#For class based views
from django.urls import path
from .views import TicketListView, TicketDetailView

# No router here — you wire each URL manually
urlpatterns = [
    path('api/tickets/', TicketListView.as_view(), name='ticket-list'),
    path('api/tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
]


#Corresponding url for DRF Function based view
# from django.urls import path
# from .views import ticket_list, ticket_detail

# urlpatterns = [
#     path('api/tickets/', ticket_list, name='ticket-list'),           # no .as_view() needed
#     path('api/tickets/<int:pk>/', ticket_detail, name='ticket-detail'),
# ]