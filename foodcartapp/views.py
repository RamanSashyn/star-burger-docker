import json
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from phonenumber_field.phonenumber import to_python
from phonenumber_field.validators import validate_international_phonenumber
from django.core.exceptions import ValidationError


from .models import Product, Order, OrderItem


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
def register_order(request):
    order_data = request.data
    products = order_data['products']
    required_fields = ['firstname', 'lastname', 'phonenumber', 'address']

    for field in required_fields:
        if field not in order_data:
            return Response({field: 'Обязательное поле.'}, status=status.HTTP_400_BAD_REQUEST)
        if order_data[field] is None or not isinstance(order_data[field], str) or not order_data[field].strip():
            return Response({field: 'Это поле не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        phone = to_python(order_data['phonenumber'])
        validate_international_phonenumber(phone)
    except ValidationError:
        return Response({'phonenumber': 'Введен некорректный номер телефона.'}, status=status.HTTP_400_BAD_REQUEST)

    if 'products' not in order_data:
        return Response({'products': ['Обязательное поле.']}, status=status.HTTP_400_BAD_REQUEST)

    if products is None:
        return Response({'products': 'Это поле не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)

    if not isinstance(products, list):
        return Response({'products': f'Ожидался list со значениями, но был получен "{type(products).__name__}".'},
                         status=status.HTTP_400_BAD_REQUEST)

    if not products:
        return Response({'products': 'Этот список не может быть пустым.'}, status=status.HTTP_400_BAD_REQUEST)

    for i, product_data in enumerate(products):
        if not isinstance(product_data, dict):
            return Response({f'products[{i}]':'Ожидался объект с ключами product и quantity.'},
                            status=status.HTTP_400_BAD_REQUEST )

        if 'product' not in product_data or not isinstance(product_data['product'], int):
            return Response({f'products[{i}].product': 'Ожидался корректный ID продукта (int).'},
                            status=status.HTTP_400_BAD_REQUEST)

        if 'quantity' not in product_data or not isinstance(product_data['quantity'], int) or product_data['quantity'] <= 0:
            return Response({f'products[{i}].quantity': 'Количество должно быть положительным числом.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if not Product.objects.filter(id=product_data['product']).exists():
            return Response({f'products[{i}].product': f'Недопустимый первичный ключ "{product_data["product"]}"'},
                            status=status.HTTP_400_BAD_REQUEST)


    order = Order.objects.create(
        first_name=order_data['firstname'],
        last_name=order_data['lastname'],
        phonenumber=order_data['phonenumber'],
        address=order_data['address'],
    )

    for item in order_data['products']:
        product = Product.objects.get(id=item['product'])
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=item['quantity'],
        )

    return Response({'status': 'success'})
