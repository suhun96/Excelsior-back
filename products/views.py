from django.views       import View
from django.http        import JsonResponse
from django.db          import transaction
from django.db.models   import Q

# Model
from users.models       import *
from products.models    import *
from users.jwtdecoder   import jwt_decoder

class CreateProductGroupView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST
        user = request.user

        try:
            if User.objects.get(id = user.id).status == False:
                return JsonResponse({'message' : 'This account is not available.'})

            new_PG , is_created = ProductGroup.objects.filter(
                Q(name = input_data['name']) | Q(code = input_data['code'])
            ).get_or_create(
                defaults= {
                    'name' : input_data['name'],
                    'code' : input_data['code'],
                    'etc'  : input_data['etc']
                })

            if is_created == False:
                return JsonResponse({'messaga' : 'The product name(product code) is already registered.'}, status = 403)      

            check_PG = list(ProductGroup.objects.filter(id = new_PG.id).values(
                'id',
                'name',
                'code',
                'etc'
            ))

            return JsonResponse({'message' : check_PG}, status = 200)
       
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)