import requests
from environs import Env
from geopy import distance as dist
from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Prefetch
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from geodata.models import Place


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


def sort_distance(item):
    _, value = item
    if isinstance(value, (int, float)):
        return (0, value)
    return (1, float('inf'))


def format_distance(value):
    if isinstance(value, (int, float)):
        if value >= 1000:
            return f"{value / 1000:.1f} км".replace('.0', '')
        return f"{int(value)} м"
    return str(value)


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return (lon, lat)


def fetch_restaurant_coordinates(apikey, places, restaurant, order_coordinates):
    try:
        if restaurant.address not in places:
            longitude, latitude = fetch_coordinates(apikey, restaurant.address)
            place = Place.objects.create(
                address=restaurant.address,
                longitude=longitude,
                latitude=latitude
            )
            distance = dist.distance(
                (latitude, longitude),
                order_coordinates
            ).meters
            places[restaurant.address] = place
            if not distance:
                return (restaurant.name, 'Ошибка получения координат')
            return (restaurant.name, distance)
        else:
            place = places[restaurant.address]
            distance = dist.distance(
                (place.latitude, place.longitude),
                order_coordinates
            ).meters
            if not distance:
                return (restaurant.name, 'Ошибка получения координат')
            return (restaurant.name, distance)
    except requests.exceptions.RequestException:
        return (restaurant.name, 'Ошибка получения координат')


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
    env = Env()
    env.read_env()
    api_key = env.str('YANDEX_API_KEY')
    places = {place.address: place for place in Place.objects.all()}
    orders = (
        Order.objects
        .calculate_total_price()
        .prefetch_related(Prefetch(
            'products__menu_items',
            queryset=(
                RestaurantMenuItem.objects
                .filter(availability=True)
                .select_related('restaurant')
            ),
            to_attr='available_menu_items'
        ))
    )
    for order in orders:
        restaurants = None
        if order.address not in places:
            order_coordinates = fetch_coordinates(api_key, order.address)
            place = Place.objects.create(
                address=order.address,
                longitude=order_coordinates[0],
                latitude=order_coordinates[1]
            )
            places[place.address] = place
        else:
            place = places[order.address]
            order_coordinates = (place.latitude, place.longitude)
        for product in order.products.all():
            available_menu_items = getattr(product, 'available_menu_items', [])
            if restaurants is None:
                restaurants = {
                    item.restaurant for item in available_menu_items}
            else:
                restaurants.intersection_update(
                    item.restaurant for item in available_menu_items)
        restaurants = sorted(
            [fetch_restaurant_coordinates(
                api_key,
                places,
                restaurant,
                order_coordinates
            ) for restaurant in restaurants],
            key=sort_distance
        )
        order.restaurants = [
            (name, format_distance(distance)) for name, distance in restaurants
        ]

    return render(request, template_name='order_items.html', context={
        'order_items': orders
    })
