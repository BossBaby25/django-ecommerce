from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import Product
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Product, Cart
from django.middleware.csrf import get_token
from django.db.models import Sum
from django.contrib.auth.models import AnonymousUser

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "errors": form.errors}, status=400)

    form = RegisterForm()
    return render(request, "store/register.html", {"form": form})


# User Login View
def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('profile')
    else:
        form = AuthenticationForm()
    return render(request, 'store/login.html', {'form': form})

# User Logout View
def user_logout(request):
    logout(request)
    return redirect('login')


def delete_product(request, product_id):
    product = Product.objects.get(id=product_id)
    product.delete()
    return redirect('home')

@login_required
def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def profile(request):
    cart_count = Cart.objects.filter(user=request.user).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    return render(request, 'store/profile.html', {'user': request.user, 'cart_count': cart_count})

def home(request):
    products = Product.objects.all()
    
    cart_count = 0
    if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
        cart_count = Cart.objects.filter(user=request.user).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    return render(request, "store/home.html", {"products": products, "cart_count": cart_count})
@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.total_price() for item in cart_items)
    cart_count = cart_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0  # Get total quantity
    return render(request, "store/cart.html", {"cart_items": cart_items, "total_price": total_price, "cart_count": cart_count})

@login_required
def add_to_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = get_object_or_404(Product, id=product_id)

        cart_item = Cart.objects.filter(user=request.user, product=product).first()

        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
        else:
            cart_item = Cart.objects.create(user=request.user, product=product, quantity=1)

        total_quantity = Cart.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_price = sum(item.total_price() for item in Cart.objects.filter(user=request.user))

        return JsonResponse({
            "cart_count": total_quantity,  # Send total quantity
            "new_quantity": cart_item.quantity,
            "new_total": cart_item.total_price(),
            "total_price": total_price
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def decrease_quantity(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        cart_item = Cart.objects.filter(user=request.user, product_id=product_id).first()

        if cart_item:
            cart_item.quantity -= 1
            if cart_item.quantity <= 0:
                cart_item.delete()
            else:
                cart_item.save()

        total_quantity = Cart.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_price = sum(item.total_price() for item in Cart.objects.filter(user=request.user))

        return JsonResponse({
            "cart_count": total_quantity,
            "new_quantity": cart_item.quantity if cart_item else 0,
            "new_total": cart_item.total_price() if cart_item else 0,
            "total_price": total_price
        })

@login_required
def remove_from_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        Cart.objects.filter(user=request.user, product_id=product_id).delete()

        total_quantity = Cart.objects.filter(user=request.user).aggregate(Sum('quantity'))['quantity__sum'] or 0
        total_price = sum(item.total_price() for item in Cart.objects.filter(user=request.user))

        return JsonResponse({
            "cart_count": total_quantity,
            "total_price": total_price
        })
