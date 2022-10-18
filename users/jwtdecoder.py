import jwt

from django.http                import JsonResponse
from users.models               import User
from excelsior_backend.settings import SECRET_KEY, ALGORITHM

def jwt_decoder(func):
    def wrapper(self, request, *args, **kwargs):
        try:
            jwt_token   = request.headers.get('Authorization', None)
            payload     = jwt.decode(jwt_token, SECRET_KEY, ALGORITHM)
            user        = User.objects.get(id = payload['user_id'])
            request.user = user

        except jwt.InvalidSignatureError:
            return JsonResponse({'message' : 'INVALID_SIGNATURE_ERROR'}, status = 400)

        except jwt.exceptions.DecodeError:
            return JsonResponse({'message' : 'INVALID_TOKEN'}, status = 400)
        
        except jwt.ExpiredSignatureError:
            return JsonResponse({"message": "EXPIRED_TOKEN"}, status=400)

        except User.DoesNotExist:
            return JsonResponse({'message': 'INVALID_USER'}, status = 400)

        
        return func(self, request, *args, **kwargs)
    return wrapper