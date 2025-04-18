from django.db import models
from django.db.models import Prefetch, F, Sum
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField


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

    def calculate_total_price(self):
        return (
            self
            .prefetch_related(
                Prefetch(
                    'items',
                    queryset=OrderItem.objects.select_related('product')
                )
            )
            .annotate(
                total_cost=Sum(
                    F('items__quantity') * F('items__price')
                )
            )
        )


class Order(models.Model):
    firstname = models.CharField(
        'Имя',
        max_length=70
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=70
    )
    phonenumber = PhoneNumberField(
        'Номер'
    )
    address = models.CharField(
        'Адрес',
        max_length=150
    )
    products = models.ManyToManyField(
        Product,
        through='OrderItem',
        verbose_name='Содержание заказа',
        blank=True
    )
    status = models.CharField(
        'статус',
        max_length=4,
        choices=[
            ('PROC', 'Обработанный'),
            ('UNPR', 'Необработанный'),
            ('COOK', 'Готовится')
        ],
        default='UNPR'
    )
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=4,
        choices=[
            ('CARD', 'Электронно'),
            ('CASH', 'Наличностью')
        ],
        default='CASH'
    )
    comment = models.CharField(
        max_length=200,
        blank=True
    )
    cooking_now = models.ForeignKey(
        Restaurant,
        verbose_name='Готовит сейчас',
        null=True,
        blank=True,
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        'Заказ создан',
        auto_now_add=True
    )
    called_at = models.DateTimeField(
        'Вреия звонка',
        blank=True,
        null=True
    )
    delivered_at = models.DateTimeField(
        'Доставлено',
        blank=True,
        null=True
    )

    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ на имя {self.firstname}'


class OrderItem(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Продукт'
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    quantity = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    def __str__(self):
        return f'Часть заказа: {self.order}'
