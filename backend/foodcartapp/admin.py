from django.contrib import admin
from django.shortcuts import redirect
from django.templatetags.static import static
from django.utils.html import format_html
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Prefetch

from .models import Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from .models import Order
from .models import OrderItem


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',
    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderItemsInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ['product', 'get_image', 'quantity']
    fields = ['product', 'get_image', 'price', 'quantity']
    extra = 0

    def get_image(self, obj):
        return format_html(
            '<img src="{}" style="max-height:200px; max-width:200px;" />',
            obj.product.image.url
        )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemsInline,]
    list_display = ['firstname', 'phonenumber', 'address']
    fields = [
        'status',
        'firstname',
        'lastname',
        'phonenumber',
        'address',
        'comment',
        'cooking_now',
        'payment_method',
        'created_at',
        'called_at',
        'delivered_at'
    ]
    readonly_fields = ['created_at']

    def response_change(self, request, obj):
        res = super().response_post_save_change(request, obj)
        next_url = request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            request.get_host()
        ):
            return redirect(next_url)
        else:
            return res

    def save_model(self, request, obj, form, change):
        if obj.cooking_now:
            obj.status = 'COOK'
        elif not obj.cooking_now and obj.status != 'PROC':
            obj.status = 'UNPR'
        return super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change, **kwargs)
        if obj:
            products = obj.products.prefetch_related(
                Prefetch(
                    'menu_items',
                    queryset=(
                        RestaurantMenuItem.objects
                        .filter(availability=True)
                        .select_related('restaurant')
                    ),
                    to_attr='available_menu_items'
                )
            )
            restaurants = None
            for product in products:
                available_menu_items = getattr(product, 'available_menu_items', [])
                if restaurants is None:
                    restaurants = {
                        item.restaurant.id for item in available_menu_items}
                else:
                    restaurants.intersection_update(
                        item.restaurant.id for item in available_menu_items)
            form.base_fields['cooking_now'].queryset = (
                Restaurant
                .objects
                .filter(id__in=list(restaurants))
            )
        return form
