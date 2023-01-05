"""excelsior_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls    import path, include
from users.views    import *


# Swagger
# from rest_framework import permissions
# from drf_yasg       import openapi
# from drf_yasg.views import get_schema_view

# schema_view = get_schema_view(
#    openapi.Info(
#       title="YAMUZIN-BACKEND-API",
#       default_version='v1',
#       description="API TEST",
#    ),
#    public=True,
#    permission_classes=[permissions.AllowAny],
# )



urlpatterns = [
    # # Swagger
    # path(r'swagger(?P<format>\.json|\.yaml)', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    # path(r'swagger', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path(r'redoc', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # django
    path('health', HealthCheckView.health),
    path('user/', include('users.urls')),
    path('product/', include('products.urls')),  
    path('warehouse/', include('locations.urls')),
    path('company/', include('companies.urls')),
    path('stock/', include('stock.urls'))
]
