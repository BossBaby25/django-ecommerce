from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import Product, Category, Cart, Order
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.db.models import Sum, Q
from django.contrib.auth.models import AnonymousUser
import time
from django.contrib import messages
from django.db import transaction
from .forms import FeedbackForm
from .models import Feedback

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

def user_login(request):
    if "failed_attempts" not in request.session:
        request.session["failed_attempts"] = 0
        request.session["lockout_time"] = 0

    failed_attempts = request.session["failed_attempts"]
    lockout_time = request.session["lockout_time"]

    if lockout_time > time.time():
        return JsonResponse({"error": f"Too many failed attempts. Try again in {int(lockout_time - time.time())} seconds."}, status=403)

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            request.session["failed_attempts"] = 0
            return redirect("profile")

        else:
            request.session["failed_attempts"] += 1
            request.session.modified = True

            if request.session["failed_attempts"] >= 3:
                request.session["lockout_time"] = time.time() + (30 * request.session["failed_attempts"])
                return JsonResponse({"error": f"Too many failed attempts. Try again in {30 * failed_attempts} seconds."}, status=403)

    else:
        form = AuthenticationForm()

    return render(request, "store/login.html", {"form": form})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def profile(request):
    cart_count = Cart.objects.filter(user=request.user).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
    orders = Order.objects.filter(user=request.user).order_by("-created_at")

    feedback_form = FeedbackForm()
    if request.method == "POST":
        feedback_form = FeedbackForm(request.POST)
        if feedback_form.is_valid():
            feedback = feedback_form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, "Thank you for your feedback!")
            feedback_form = FeedbackForm()

    return render(request, 'store/profile.html', {
        'user': request.user,
        'cart_count': cart_count,
        'orders': orders,
        'feedback_form': feedback_form
    })


def home(request):
    products = Product.objects.all()
    categories = Category.objects.all()


    category_filter = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if category_filter:
        products = products.filter(category__name=category_filter)
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    cart_count = 0
    if request.user.is_authenticated and not isinstance(request.user, AnonymousUser):
        cart_count = Cart.objects.filter(user=request.user).aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0

    return render(request, "store/home.html", {
        "products": products,
        "cart_count": cart_count,
        "categories": categories
    })

@login_required
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    total_price = sum(item.total_price() for item in cart_items)
    cart_count = cart_items.aggregate(total_quantity=Sum('quantity'))['total_quantity'] or 0
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
            "cart_count": total_quantity,
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

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect("cart")

    total_price = sum(item.total_price() for item in cart_items)

    product_info_list = []
    for item in cart_items:
        product_info_list.append(f"{item.product.name} (x{item.quantity})")
    products_info_str = ", ".join(product_info_list)

    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            products_info=products_info_str
        )

        cart_items.delete()

    request.session["checkout_success"] = "Your order has been placed successfully!"
    return redirect("profile")
