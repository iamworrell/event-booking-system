#Django Class Based View - Raw Django
import json
from django.http import JsonResponse
from django.views import View
from django.db import transaction
from .models import Users


class UserListView(View):
    def get(self, request):
        users = list(Users.objects.values('user_id', 'first_name', 'last_name', 'date_of_birth'))
        for user in users:
            user['date_of_birth'] = str(user['date_of_birth'])
        return JsonResponse(users, safe=False, status=200)

    def post(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        required_fields = ['first_name', 'last_name', 'date_of_birth']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return JsonResponse({'detail': f'Missing required fields: {", ".join(missing)}'}, status=400)

        try:
            with transaction.atomic():
                user = Users.objects.create(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    date_of_birth=data['date_of_birth'],
                )
        except Exception as e:
            return JsonResponse({'detail': f'Failed to create user: {str(e)}'}, status=500)

        return JsonResponse({
            'user_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_of_birth': str(user.date_of_birth),
        }, status=201)


class UserDetailView(View):
    def _get_user(self, pk):
        try:
            return Users.objects.get(pk=pk), None
        except Users.DoesNotExist:
            return None, JsonResponse({'detail': 'User not found.'}, status=404)

    def _serialize(self, user):
        return {
            'user_id': user.user_id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'date_of_birth': str(user.date_of_birth),
        }

    def get(self, request, pk):
        user, error = self._get_user(pk)
        if error:
            return error
        return JsonResponse(self._serialize(user), status=200)

    def put(self, request, pk):
        user, error = self._get_user(pk)
        if error:
            return error

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        required_fields = ['first_name', 'last_name', 'date_of_birth']
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return JsonResponse({'detail': f'Missing required fields: {", ".join(missing)}'}, status=400)

        try:
            with transaction.atomic():
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.date_of_birth = data['date_of_birth']
                user.save()
        except Exception as e:
            return JsonResponse({'detail': f'Failed to update user: {str(e)}'}, status=500)

        return JsonResponse(self._serialize(user), status=200)

    def patch(self, request, pk):
        user, error = self._get_user(pk)
        if error:
            return error

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON.'}, status=400)

        updatable_fields = ['first_name', 'last_name', 'date_of_birth']
        try:
            with transaction.atomic():
                for field in updatable_fields:
                    if field in data:
                        setattr(user, field, data[field])
                user.save()
        except Exception as e:
            return JsonResponse({'detail': f'Failed to update user: {str(e)}'}, status=500)

        return JsonResponse(self._serialize(user), status=200)

    def delete(self, request, pk):
        user, error = self._get_user(pk)
        if error:
            return error

        try:
            with transaction.atomic():
                user.delete()
        except Exception as e:
            return JsonResponse({'detail': f'Failed to delete user: {str(e)}'}, status=500)

        return JsonResponse({}, status=204)
