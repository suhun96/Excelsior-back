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

        try:
            if User.objects.get(id = request.user.id ).status == False:
                return JsonResponse({'message' : 'This account is not available.'}, status = 403)

            if not "name" in input_data or not "code" in input_data:
                return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)

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


class CreateCompanyView(View):
    @jwt_decoder
    def post(self, request):
        input_data = request.POST

        try:
            if User.objects.get(id = request.user.id ).status == False:
                return JsonResponse({'message' : 'This account is not available.'}, status = 403)

            if not "name" in input_data or not "code" in input_data:
                return JsonResponse({'message' : 'Please enter the correct value.'}, status = 403)

            new_CP , is_created = Company.objects.filter(
                Q(name = input_data['name']) | Q(code = input_data['code'])
            ).get_or_create(
                defaults= {
                    'name'       : input_data['name'],
                    'code'       : input_data['code'],
                    'address'    : input_data['address'],
                    'managers'   : input_data['managers'],
                    'telephone'  : input_data['telephone'],
                    'mobilephone': input_data['mobilephone'],
                    'manage_tag' : input_data['manage_tag'],
                    'etc'        : input_data['etc']
                })

            if is_created == False:
                return JsonResponse({'messaga' : 'The product name(product code) is already registered.'}, status = 403)      

            check_CP = list(Company.objects.filter(id = new_CP.id).values(
                'name',       
                'code',      
                'address',    
                'managers',   
                'telephone',  
                'mobilephone',
                'manage_tag', 
                'etc'        
            ))

            return JsonResponse({'message' : check_CP}, status = 200)
       
        except KeyError:
            return JsonResponse({'message' : 'KEY ERROR'}, status = 403)