from rest_framework import serializers
from django.db import transaction

from .models import Order, OrderItem, Product


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )
    quantity = serializers.IntegerField()

    class Meta:
        model = OrderItem
        fields = ('product', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products'
        )

    def validate_products(self, value):
        if not value:
            raise serializers.ValidationError(
                "Этот список не может быть пустым.")
        return value

    def create(self, validated_data):
        try:
            with transaction.atomic():
                products = validated_data.pop('products')
                order = Order.objects.create(**validated_data)
                for product in products:
                    OrderItem.objects.create(order=order, **product)
        except Exception as e:
            print(f'error while creating order: {e}')
        return order
