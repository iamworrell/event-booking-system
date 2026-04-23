#Django Rest Framework Function Based
from django.urls import path
from .views import ReservationListView, reservation_list, reservation_detail

urlpatterns = [
    path('api/reservations-class/', ReservationListView.as_view(), name='reservation-list-class'),
    path('api/reservations/', reservation_list, name='reservation-list'),
    path('api/reservations/<int:pk>/', reservation_detail, name='reservation-detail'),
]
#For Django Rest Framework using Model View Sets Only
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import ReservationViewSet

# router = DefaultRouter()
# router.register(r'reservations', ReservationViewSet, basename='reservation')

# urlpatterns = [
#     path('api/', include(router.urls)),
# ]