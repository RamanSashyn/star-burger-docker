from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, F
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.utils import fetch_coordinates, get_distance_km
from foodcartapp.models import Product, Restaurant, Order, OrderItem, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {item.restaurant_id: item.availability for item in product.menu_items.all()}
        ordered_availability = [availability.get(restaurant.id, False) for restaurant in restaurants]

        products_with_restaurant_availability.append(
            (product, ordered_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurant_availability': products_with_restaurant_availability,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    menu_items = RestaurantMenuItem.objects.select_related('restaurant', 'product').filter(availability=True)

    orders = (
        Order.objects
        .with_total_price()
        .exclude(status=Order.DONE)
        .prefetch_related('items__product')
        .select_related('cooking_restaurant')
        .order_by('-id')
    )

    restaurant_coords = {}
    for item in menu_items:
        restaurant = item.restaurant
        if restaurant.address not in restaurant_coords:
            coords = fetch_coordinates(restaurant.address)
            if coords:
                restaurant_coords[restaurant.address] = coords

    order_items = []
    for order in orders:
        order_coords = fetch_coordinates(order.address)
        order_products = [item.product for item in order.items.all()]

        product_restaurants = {}
        for item in menu_items:
            if item.product in order_products:
                product_restaurants.setdefault(item.product, set()).add(item.restaurant)

        if product_restaurants:
            possible_restaurants = set.intersection(*product_restaurants.values())
        else:
            possible_restaurants = set()

        restaurant_distances = []
        if order_coords:
            for restaurant in possible_restaurants:
                coords = restaurant_coords.get(restaurant.address)
                if coords:
                    distance = get_distance_km(order_coords, coords)
                    restaurant_distances.append((restaurant, distance))
            restaurant_distances.sort(key=lambda x: x[1])

        if order.cooking_restaurant:
            restaurant_text = f'Готовит {order.cooking_restaurant.name}'
        elif order_coords and restaurant_distances:
            restaurant_text = (
                '<details><summary>Может быть приготовлен ресторанами</summary><ul>' +
                ''.join([f'<li>{r.name} — {d} км</li>' for r, d in restaurant_distances]) +
                '</ul></details>'
            )
        elif not order_coords:
            restaurant_text = 'Ошибка определения координат'
        else:
            restaurant_text = 'Нет ресторанов для приготовления'

        order_items.append({
            'id': order.id,
            'status': order.get_status_display(),
            'payment_method': order.get_payment_method_display(),
            'total_price': order.total_price,
            'client': f'{order.first_name} {order.last_name}',
            'phonenumber': order.phonenumber,
            'address': order.address,
            'comment': order.comment,
            'restaurants': restaurant_text,
        })

    return render(request, template_name='order_items.html', context={
        'order_items': order_items,
    })
