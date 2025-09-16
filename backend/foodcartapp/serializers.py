from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from .models import Product, Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all()
    )

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    phonenumber = PhoneNumberField()
    products = OrderItemSerializer(many=True, allow_empty=False, write_only=True)

    class Meta:
        model = Order
        fields = ['id', 'firstname', 'lastname', 'phonenumber', 'address', 'products']


    def create(self, validated_data):
        product_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)

        order_items = []
        for item in product_data:
            product = item['product']
            order_items.append(OrderItem(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=product.price,
            ))

        OrderItem.objects.bulk_create(order_items)
        return order
