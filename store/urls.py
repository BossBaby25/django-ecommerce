from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .views import home, add_to_cart, remove_from_cart, cart_view , decrease_quantity , checkout

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('', home, name='home'),
    path('cart/', cart_view, name='cart'),
    path('add-to-cart/', add_to_cart, name="add_to_cart"),
    path("remove-from-cart/", remove_from_cart, name="remove_from_cart"),
    path("decrease-quantity/", decrease_quantity, name="decrease_quantity"),
    path("checkout/", checkout, name="checkout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)