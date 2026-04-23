#For Django Rest Framework Function Based
from django.urls import path
from .views import event_list, event_detail

urlpatterns = [
    path('api/events/', event_list, name='event-list'),
    path('api/events/<int:pk>/', event_detail, name='event-detail'),
]


#For Django Rest Framework with ModelViewSets
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import EventViewSet

# router = DefaultRouter()
# router.register(r'events', EventViewSet, basename='event')

# urlpatterns = [
#     path('api/', include(router.urls)),
# ]