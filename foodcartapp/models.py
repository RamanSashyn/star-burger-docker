from django.db import models
from django.db.models import Sum, DecimalField, F
from django.core.validators import MinValueValidator
from django.utils.timezone import now
from phonenumber_field.modelfields import PhoneNumberField
from decimal import Decimal


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(
                F('items__quantity') * F('items__product__price'),
                output_field=DecimalField()
            )
        )


class Order(models.Model):
    NEW = 'new'
    CONFIRMED = 'confirmed'
    COOKING = 'cooking'
    DELIVERING = 'delivering'
    DONE = 'done'
    CASH = 'cash'
    ELECTRONIC = 'electronic'

    STATUS_CHOICES = [
        (NEW, 'Новый'),
        (CONFIRMED, 'Подтверждён'),
        (COOKING, 'Готовится'),
        (DELIVERING, 'Доставляется'),
        (DONE, 'Выполнен'),
    ]

    PAYMENT_CHOICES = [
        (CASH, 'Наличностью'),
        (ELECTRONIC, 'Электронно'),
    ]

    first_name = models.CharField(
        'имя',
        max_length=20
    )
    last_name = models.CharField(
        'фамилия',
        max_length=20
    )
    phonenumber = PhoneNumberField(
        'номер телефона',
        db_index=True,
    )
    address = models.CharField(
        'адрес',
        max_length=100
    )
    status = models.CharField(
        verbose_name='статус',
        choices=STATUS_CHOICES,
        default=NEW,
        max_length=20,
        db_index=True,
    )
    payment_method = models.CharField(
        'способ оплаты',
        choices=PAYMENT_CHOICES,
        max_length=20,
        default=CASH,
        db_index=True,
    )
    cooking_restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='ресторан для приготовления',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='orders',
    )
    comment = models.TextField(
        'комментарий',
        blank=True,
    )
    created_at = models.DateTimeField(
        'время оформления',
        auto_now_add=True,
        db_index=True,
    )
    called_at = models.DateTimeField(
        'время звонка клиенту',
        null=True,
        blank=True,
        db_index=True,
    )
    delivered_at = models.DateTimeField(
        'время доставки',
        null=True,
        blank=True,
        db_index=True,
    )

    objects = OrderQuerySet.as_manager()

    def __str__(self):
        return f'Заказ №{self.id} от {self.first_name} {self.last_name}'

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE, verbose_name='товар')
    quantity = models.PositiveIntegerField('количество')
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )

    def __str__(self):
        return f'{self.quantity} x {self.product.name} (заказ {self.order.id})'

    class Meta:
        verbose_name = 'позиция заказа'
        verbose_name_plural = 'позиции заказа'
