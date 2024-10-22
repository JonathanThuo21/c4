from django.db import models
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django.utils.text import slugify
from .utils import reverse_geocode


class Location(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    location_name = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Reverse geocode the location to get the name
        if not self.location_name:
            self.location_name = reverse_geocode(self.latitude, self.longitude)
        super().save(*args, **kwargs)

# Banner
class Banner(models.Model):
    img=models.ImageField(upload_to="banner_imgs/")
    alt_text=models.CharField(max_length=300)
    title = models.CharField(max_length=255, null=True, blank=True)
    subtitle = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural='1. Banners'

    def image_tag(self):
        return mark_safe('<img src="%s" width="100" />' % (self.img.url))

    def __str__(self):
        return self.alt_text
    

# Featured Images
class Featured(models.Model):
    img=models.ImageField(upload_to="featured_imgs/")
    alt_text=models.CharField(max_length=300)
    

    class Meta:
        verbose_name_plural='1. Featured'

    def image_tag(self):
        return mark_safe('<img src="%s" width="100" />' % (self.img.url))

    def __str__(self):
        return self.alt_text

# Category
class Category(models.Model):
    title=models.CharField(max_length=100)
    image=models.ImageField(upload_to="cat_imgs/")

    class Meta:
        verbose_name_plural='2. Categories'

    def image_tag(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

    def __str__(self):
        return self.title







# Product Model
class Product(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=400, unique=True, blank=True)  # SlugField instead of CharField
    detail = models.TextField()
    specs = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = '6. Products'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  # Auto-generate slug from title if not provided
        super().save(*args, **kwargs)


# Product Attribute
class ProductAttribute(models.Model):
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    price=models.PositiveIntegerField(default=0)
    image=models.ImageField(upload_to="product_imgs/",null=True)

    class Meta:
        verbose_name_plural='7. ProductAttributes'

    def __str__(self):
        return self.product.title

    def image_tag(self):
        return mark_safe('<img src="%s" width="50" height="50" />' % (self.image.url))

# Order
status_choice=(
        ('In progress','In Process'),
        ('On the Way','Shipped'),
        ('delivered','Delivered'),
    )

class CartOrder(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    total_amt=models.FloatField()
    paid_status=models.BooleanField(default=False)
    order_dt=models.DateTimeField(auto_now_add=True)
    order_status=models.CharField(choices=status_choice,default='In Progress',max_length=150)
    location = models.ForeignKey('Location', on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        # Automatically assign the latest location of the user if not already set
        if not self.location:
            latest_location = Location.objects.filter(user=self.user).last()
            if latest_location:
                self.location = latest_location
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural='8. Orders'

# OrderItems
class CartOrderItems(models.Model):
    order=models.ForeignKey(CartOrder,on_delete=models.CASCADE)
    invoice_no=models.CharField(max_length=150)
    item=models.CharField(max_length=150)
    image=models.CharField(max_length=200)
    qty=models.IntegerField()
    price=models.FloatField()
    total=models.FloatField()

    class Meta:
        verbose_name_plural='9. Order Items'

    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="50" height="50" />' % (self.image))

# Product Review
RATING=(
    (1,'1'),
    (2,'2'),
    (3,'3'),
    (4,'4'),
    (5,'5'),
)
class ProductReview(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    review_text=models.TextField()
    review_rating=models.CharField(choices=RATING,max_length=150)

    class Meta:
        verbose_name_plural='Reviews'

    def get_review_rating(self):
        return self.review_rating

# WishList
class Wishlist(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural='Wishlist'

class UserAddressBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=50, null=True, blank=True)  # Updated field name
    address = models.TextField()
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'AddressBook'
    