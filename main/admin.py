from django.contrib import admin
from .models import Banner, Featured, Category,Product,ProductAttribute,CartOrder,CartOrderItems,ProductReview,Wishlist,UserAddressBook
from django.contrib import admin
from .models import Location



class LocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'location_name')
    search_fields = ('location_name', 'user__username')
    list_filter = ('location_name', 'user')

admin.site.register(Location, LocationAdmin)



class BannerAdmin(admin.ModelAdmin):
	list_display=('alt_text','image_tag')
admin.site.register(Banner,BannerAdmin)

class FeaturedAdmin(admin.ModelAdmin):
	list_display=('alt_text','image_tag')
admin.site.register(Featured,FeaturedAdmin)

class CategoryAdmin(admin.ModelAdmin):
	list_display=('title','image_tag')
admin.site.register(Category,CategoryAdmin)



class ProductAdmin(admin.ModelAdmin):
    list_display=('id','title','category','status','is_featured')
    list_editable=('status','is_featured')
admin.site.register(Product,ProductAdmin)

# Product Attribute
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display=('id','image_tag','product','price')
admin.site.register(ProductAttribute,ProductAttributeAdmin)

# Order
class CartOrderItemsInline(admin.TabularInline):
    model = CartOrderItems
    extra = 1  # Number of empty forms to display
    fields = ('invoice_no', 'item', 'image_tag', 'qty', 'price', 'total')
    readonly_fields = ('image_tag',)  # Make image_tag read-only

    def get_extra(self, request, obj=None, **kwargs):
        if obj:  # If editing an existing order, show all related items
            return 0
        return super().get_extra(request, obj, **kwargs)

    def image_tag(self, obj):
        return obj.image_tag()
    image_tag.short_description = 'Image'

class CartOrderAdmin(admin.ModelAdmin):
    list_editable = ('paid_status', 'order_status')
    list_display = ('user', 'total_amt', 'paid_status', 'order_dt', 'order_status', 'get_location_name', 'get_location_coordinates')
    inlines = [CartOrderItemsInline]  # Include the inline admin for CartOrderItems
    search_fields = ('user__username', 'order_status', 'total_amt')  # Fields to search
    list_filter = ('paid_status', 'order_status', 'location')  # Fields to filter by
    
    def get_location_name(self, obj):
        if obj.location:
            print(f"Location Name: {obj.location.location_name}")  # Debugging print
            return obj.location.location_name
        return 'N/A'
    get_location_name.short_description = 'Location Name'

    def get_location_coordinates(self, obj):
        if obj.location:
            print(f"Coordinates: Lat: {obj.location.latitude}, Lon: {obj.location.longitude}")  # Debugging print
            return f"Lat: {obj.location.latitude}, Lon: {obj.location.longitude}"
        return 'N/A'
    get_location_coordinates.short_description = 'Coordinates'

admin.site.register(CartOrder, CartOrderAdmin)

class CartOrderItemsAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', 'item', 'image_tag', 'qty', 'price', 'total')

admin.site.register(CartOrderItems, CartOrderItemsAdmin)

class ProductReviewAdmin(admin.ModelAdmin):
	list_display=('user','product','review_text','get_review_rating')
admin.site.register(ProductReview,ProductReviewAdmin)


admin.site.register(Wishlist)


class UserAddressBookAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address', 'status')  # Updated to include phone_number

admin.site.register(UserAddressBook, UserAddressBookAdmin)