import re
from django.http                import JsonResponse
from users.models               import User

def check_status(func):
    def wrapper(self, request, *args, **kwargs):
        user_status = User.objects.get(id = request.user.id ).status
        
        if user_status == False:
            return JsonResponse({'message' : 'This account is not available.'}, status = 403)
        
        else:
            return func(self, request, *args, **kwargs)

    return wrapper