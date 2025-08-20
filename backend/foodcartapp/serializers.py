from rest_framework import serializers
from django.db import transaction
from environs import Env

from .models import Order, OrderItem, Product
from geodata.models import Place
from restaurateur.views import fetch_coordinates


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ('product', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(
        many=True,
        write_only=True,
        source=None,
        required=True
    )

    class Meta:
        model = Order
        fields = (
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products'
        )

    def create(self, validated_data):
        try:
            with transaction.atomic():
                products = validated_data.pop('products')
                order = Order.objects.create(**validated_data)
                for item in products:
                    product = item['product']
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item['quantity'],
                        price=product.price
                    )
            env = Env()
            env.read_env()
            api_key = env.str('YANDEX_API_KEY')
            places = {place.address: place for place in Place.objects.all()}
            if order.address not in places:
                try:
                    longitude, latitude = fetch_coordinates(
                        api_key,
                        order.address
                    )
                except Exception:
                    longitude = 0.0
                    latitude = 0.0
                Place.objects.create(
                    address=order.address,
                    longitude=longitude,
                    latitude=latitude
                )
        except Exception as e:
            print(f'error while creating order: {e}')
        return order
