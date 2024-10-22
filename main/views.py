from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse,HttpResponse
from .models import Banner,Category, Featured, Product,ProductAttribute,CartOrder,CartOrderItems,ProductReview,Wishlist,UserAddressBook
from django.db.models import Max,Min,Count,Avg
from django.db.models.functions import ExtractMonth
from django.contrib.auth.forms import PasswordChangeForm
from django.template.loader import render_to_string
from .forms import SignupForm,ReviewAdd,AddressBookForm,ProfileForm
from django.contrib.auth import login,authenticate
from django.contrib.auth.decorators import login_required
import json
from .models import Location
from twilio.rest import Client
from .forms import CartOrderForm, CartOrderItemsForm, UserAddressBookForm

#paypal
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from .utils import reverse_geocode


@staff_member_required
def custom_admin_view(request):
    orders = CartOrder.objects.all().order_by('-order_dt')
    order_items = CartOrderItems.objects.all()
    addresses = UserAddressBook.objects.all()
    
    
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('order_status')
        
        # Update order status
        order = CartOrder.objects.get(id=order_id)
        if new_status in ['In progress', 'On the Way', 'delivered']:
            order.order_status = new_status
            order.save()
        
        # Redirect back to the admin panel after update
        return redirect('custom_admin_view')
    

    if request.method == "POST":
        if "edit_order" in request.POST:
            order = get_object_or_404(CartOrder, id=request.POST.get("order_id"))
            form = CartOrderForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                messages.success(request, "Order updated successfully!")
                return redirect("custom_admin_view")

        elif "edit_order_item" in request.POST:
            item = get_object_or_404(CartOrderItems, id=request.POST.get("item_id"))
            form = CartOrderItemsForm(request.POST, instance=item)
            if form.is_valid():
                form.save()
                messages.success(request, "Order item updated successfully!")
                return redirect("custom_admin_view")

        elif "edit_address" in request.POST:
            address = get_object_or_404(UserAddressBook, id=request.POST.get("address_id"))
            form = UserAddressBookForm(request.POST, instance=address)
            if form.is_valid():
                form.save()
                messages.success(request, "Address updated successfully!")
                return redirect("custom_admin_view")

    context = {
        'orders': orders,
        'order_items': order_items,
        'addresses': addresses,
        'order_form': CartOrderForm(),
        'order_item_form': CartOrderItemsForm(),
        'address_form': UserAddressBookForm(),
    }
    return render(request, 'custom_admin_page.html', context)


def add_location(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        # Create and save the location
        location = Location(latitude=latitude, longitude=longitude)
        location.location_name = reverse_geocode(latitude, longitude)
        location.save()

        return redirect('some_view_name')

    return render(request, 'add_location.html')

@login_required
def get_locations(request):
    # Fetch locations associated with the logged-in user
    locations = Location.objects.filter(user=request.user).values('latitude', 'longitude', 'location_name')
    return JsonResponse(list(locations), safe=False)


@csrf_exempt
@login_required  # Ensure only logged-in users can send locations
def send_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            # Reverse geocode to get the location name
            location_name = reverse_geocode(latitude, longitude)

            # Create and save the location associated with the user
            location = Location.objects.create(
                user=request.user,  # Associate with the logged-in user
                latitude=latitude,
                longitude=longitude,
                location_name=location_name
            )

            return JsonResponse({'status': 'success', 'latitude': latitude, 'longitude': longitude, 'location_name': location_name})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

@login_required(login_url='login')
# Home Page
def home(request):
    
    
    # Get banners and featured products
    banners = Banner.objects.all().order_by('-id')
    featured_images = Featured.objects.all().order_by('-id')
    data = Product.objects.filter(is_featured=True).order_by('-id')
    
    order = CartOrder.objects.filter(user=request.user).last()
    order_status = order.order_status if order else None

    # Cart Data
    total_amt = 0
    cart_data = request.session.get('cartdata', {})
    
    for item in cart_data.values():
        qty = item.get('qty', 0)
        price_str = item.get('price', '0')
        try:
            price = float(price_str)
        except ValueError:
            price = 0
        total_amt += int(qty) * price
        
        # WhatsApp Button Data
    # WhatsApp Button Data
    try:
        # Fetch the User instance for "Jonathan"
        user = User.objects.get(username="Jonathan")
        # Retrieve UserAddressBook entry for this user
        address_book_entry = UserAddressBook.objects.get(user=user)
        phone_number = address_book_entry.phone_number
    except (User.DoesNotExist, UserAddressBook.DoesNotExist):
        phone_number = None
    
    # Build the message template dynamically
    if order:
        cart_items = CartOrderItems.objects.filter(order=order)
        item_details = []
        
        for item in cart_items:
            item_details.append(f"{item.item} x {item.qty}")
        
        item_details_str = "\n".join(item_details)
        dynamic_message = f"Hi, I wanted to enquire about the following products from your online catalog:\n\n{item_details_str}"
    else:
        dynamic_message = "I'd like to make an enquiry."
    
    if phone_number:
        # Prepare WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone_number}?text={dynamic_message.replace(' ', '%20').replace('\n', '%0A')}"
    else:
        whatsapp_url = None
            
        
    # Render the home page with cart and product data
    return render(request, 'index.html', {
        'data': data,
        'banners': banners,
        'featured_images': featured_images,
        'order_status': order_status,
        'cart_data': cart_data,
        'whatsapp_url': whatsapp_url,
        'totalitems': len(cart_data),
        'total_amt': total_amt
    })

# Category
def category_list(request):
    data=Category.objects.all().order_by('-id')
    return render(request,'category_list.html',{'data':data})


# Product List
def product_list(request):
    total_data = Product.objects.count()
    data = Product.objects.all().order_by('-id')[:3]
    min_price = ProductAttribute.objects.aggregate(Min('price'))
    max_price = ProductAttribute.objects.aggregate(Max('price'))
    
    order = CartOrder.objects.filter(user=request.user).last()
    order_status = order.order_status if order else None

    # Retrieve cart data
    cart_data = request.session.get('cartdata', {})
    total_amt = 0
    for item in cart_data.values():
        qty = item.get('qty', 0)
        price_str = item.get('price', '0')
        try:
            price = float(price_str)
        except ValueError:
            price = 0
        total_amt += int(qty) * price
        
        # WhatsApp Button Data
    try:
        # Fetch the User instance for "Jonathan"
        user = User.objects.get(username="Jonathan")
        # Retrieve UserAddressBook entry for this user
        address_book_entry = UserAddressBook.objects.get(user=user)
        phone_number = address_book_entry.phone_number
    except (User.DoesNotExist, UserAddressBook.DoesNotExist):
        phone_number = None
    
    # Build the message template dynamically
    if order:
        cart_items = CartOrderItems.objects.filter(order=order)
        item_details = []
        
        for item in cart_items:
            item_details.append(f"{item.item} x {item.qty}")
        
        item_details_str = "\n".join(item_details)
        dynamic_message = f"Hi, I wanted to enquire about the following products from your online catalog:\n\n{item_details_str}"
    else:
        dynamic_message = "I'd like to make an enquiry."
    
    if phone_number:
        # Prepare WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone_number}?text={dynamic_message.replace(' ', '%20').replace('\n', '%0A')}"
    else:
        whatsapp_url = None

    return render(request, 'product_list.html', {
        'data': data,
        'total_data': total_data,
        'order_status': order_status,
        'min_price': min_price,
        'max_price': max_price,
        'whatsapp_url': whatsapp_url,
        'cart_data': cart_data,
        'totalitems': len(cart_data),
        'total_amt': total_amt,
    })

# Product List According to Category
def category_product_list(request, cat_id):
    category = Category.objects.get(id=cat_id)
    data = Product.objects.filter(category=category).order_by('-id')
    
    order = CartOrder.objects.filter(user=request.user).last()
    order_status = order.order_status if order else None

    # Retrieve cart data
    cart_data = request.session.get('cartdata', {})
    total_amt = 0
    for item in cart_data.values():
        qty = item.get('qty', 0)
        price_str = item.get('price', '0')
        try:
            price = float(price_str)
        except ValueError:
            price = 0
        total_amt += int(qty) * price
        
        # WhatsApp Button Data
    try:
        # Fetch the User instance for "Jonathan"
        user = User.objects.get(username="Jonathan")
        # Retrieve UserAddressBook entry for this user
        address_book_entry = UserAddressBook.objects.get(user=user)
        phone_number = address_book_entry.phone_number
    except (User.DoesNotExist, UserAddressBook.DoesNotExist):
        phone_number = None
    
    # Build the message template dynamically
    if order:
        cart_items = CartOrderItems.objects.filter(order=order)
        item_details = []
        
        for item in cart_items:
            item_details.append(f"{item.item} x {item.qty}")
        
        item_details_str = "\n".join(item_details)
        dynamic_message = f"Hi, I wanted to enquire about the following products from your online catalog:\n\n{item_details_str}"
    else:
        dynamic_message = "I'd like to make an enquiry."
    
    if phone_number:
        # Prepare WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone_number}?text={dynamic_message.replace(' ', '%20').replace('\n', '%0A')}"
    else:
        whatsapp_url = None

    return render(request, 'category_product_list.html', {
        'data': data,
        'category': category,
        'order_status': order_status,
        'whatsapp_url': whatsapp_url,
        'cart_data': cart_data,
        'totalitems': len(cart_data),
        'total_amt': total_amt,
    })



# Product Detail
def product_detail(request,slug,id):
	product=Product.objects.get(id=id)
	related_products=Product.objects.filter(category=product.category).exclude(id=id)[:4]
	colors=ProductAttribute.objects.filter(product=product).values('color__id','color__title','color__color_code').distinct()
	sizes=ProductAttribute.objects.filter(product=product).values('size__id','size__title','price','color__id').distinct()
	reviewForm=ReviewAdd()

	# Check
	canAdd=True
	reviewCheck=ProductReview.objects.filter(user=request.user,product=product).count()
	if request.user.is_authenticated:
		if reviewCheck > 0:
			canAdd=False
	# End

	# Fetch reviews
	reviews=ProductReview.objects.filter(product=product)
	# End

	# Fetch avg rating for reviews
	avg_reviews=ProductReview.objects.filter(product=product).aggregate(avg_rating=Avg('review_rating'))
	# End

	return render(request, 'product_detail.html',{'data':product,'related':related_products,'colors':colors,'sizes':sizes,'reviewForm':reviewForm,'canAdd':canAdd,'reviews':reviews,'avg_reviews':avg_reviews})

# Search
def search(request):
    q = request.GET.get('q', '')
    data = Product.objects.filter(title__icontains=q).order_by('-id')
    
    order = CartOrder.objects.filter(user=request.user).last()
    order_status = order.order_status if order else None

    # Retrieve cart data
    cart_data = request.session.get('cartdata', {})
    total_amt = 0
    for item in cart_data.values():
        qty = item.get('qty', 0)
        price_str = item.get('price', '0')
        try:
            price = float(price_str)
        except ValueError:
            price = 0
        total_amt += int(qty) * price
        
        # WhatsApp Button Data
    try:
        # Fetch the User instance for "Jonathan"
        user = User.objects.get(username="Jonathan")
        # Retrieve UserAddressBook entry for this user
        address_book_entry = UserAddressBook.objects.get(user=user)
        phone_number = address_book_entry.phone_number
    except (User.DoesNotExist, UserAddressBook.DoesNotExist):
        phone_number = None
    
    # Build the message template dynamically
    if order:
        cart_items = CartOrderItems.objects.filter(order=order)
        item_details = []
        
        for item in cart_items:
            item_details.append(f"{item.item} x {item.qty}")
        
        item_details_str = "\n".join(item_details)
        dynamic_message = f"Hi, I wanted to enquire about the following products from your online catalog:\n\n{item_details_str}"
    else:
        dynamic_message = "I'd like to make an enquiry."
    
    if phone_number:
        # Prepare WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone_number}?text={dynamic_message.replace(' ', '%20').replace('\n', '%0A')}"
    else:
        whatsapp_url = None

    return render(request, 'search.html', {
        'data': data,
        'cart_data': cart_data,
        'order_status': order_status,
        'whatsapp_url': whatsapp_url,
        'totalitems': len(cart_data),
        'total_amt': total_amt,
    })

def filter_data(request):
    colors = request.GET.getlist('color[]')
    categories = request.GET.getlist('category[]')
    sizes = request.GET.getlist('size[]')
    
    # Get minPrice and maxPrice, and validate them
    minPrice = request.GET.get('minPrice')
    maxPrice = request.GET.get('maxPrice')
    
    allProducts = Product.objects.all().order_by('-id').distinct()
    
    # Check if minPrice is a valid number
    if minPrice and minPrice.isdigit():
        minPrice = int(minPrice)
        allProducts = allProducts.filter(productattribute__price__gte=minPrice)
    
    # Check if maxPrice is a valid number
    if maxPrice and maxPrice.isdigit():
        maxPrice = int(maxPrice)
        allProducts = allProducts.filter(productattribute__price__lte=maxPrice)
    
    if colors:
        allProducts = allProducts.filter(productattribute__color__id__in=colors).distinct()
    
    if categories:
        allProducts = allProducts.filter(category__id__in=categories).distinct()
    
    if sizes:
        allProducts = allProducts.filter(productattribute__size__id__in=sizes).distinct()
    
    # Render the filtered product list
    t = render_to_string('ajax/product-list.html', {'data': allProducts})
    
    return JsonResponse({'data': t})


# Load More
def load_more_data(request):
	offset=int(request.GET['offset'])
	limit=int(request.GET['limit'])
	data=Product.objects.all().order_by('-id')[offset:offset+limit]
	t=render_to_string('ajax/product-list.html',{'data':data})
	return JsonResponse({'data':t}
)

# Add to cart
def add_to_cart(request):
    cart_p = {}
    item_id = str(request.GET['id'])
    cart_p[item_id] = {
        'image': request.GET['image'],
        'title': request.GET['title'],
        'qty': request.GET['qty'],
        'price': request.GET['price'],
    }
    cart_data = request.session.get('cartdata', {})
    
    if item_id in cart_data:
        cart_data[item_id]['qty'] = int(cart_p[item_id]['qty'])
    else:
        cart_data.update(cart_p)
    
    request.session['cartdata'] = cart_data
    
    return JsonResponse({'data': cart_data, 'totalitems': len(cart_data)})

# Cart List Page
def cart_list(request):
    total_amt = 0
    cart_data = request.session.get('cartdata', {})
    
    order = CartOrder.objects.filter(user=request.user).last()
    
    for item in cart_data.values():
        qty = item.get('qty', 0)
        price_str = item.get('price', '0')
        try:
            price = float(price_str)
        except ValueError:
            price = 0
        total_amt += int(qty) * price
        
    # WhatsApp Button Data
    try:
        # Fetch the User instance for "Jonathan"
        user = User.objects.get(username="Jonathan")
        # Retrieve UserAddressBook entry for this user
        address_book_entry = UserAddressBook.objects.get(user=user)
        phone_number = address_book_entry.phone_number
    except (User.DoesNotExist, UserAddressBook.DoesNotExist):
        phone_number = None
    
    # Build the message template dynamically
    if order:
        cart_items = CartOrderItems.objects.filter(order=order)
        item_details = []
        
        for item in cart_items:
            item_details.append(f"{item.item} x {item.qty}")
        
        item_details_str = "\n".join(item_details)
        dynamic_message = f"Hi, I wanted to enquire about the following products from your online catalog:\n\n{item_details_str}"
    else:
        dynamic_message = "I'd like to make an enquiry."
    
    if phone_number:
        # Prepare WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone_number}?text={dynamic_message.replace(' ', '%20').replace('\n', '%0A')}"
    else:
        whatsapp_url = None
    
        
    
    return render(request, 'cart.html', {
        'cart_data': cart_data,
        'whatsapp_url': whatsapp_url,
        'totalitems': len(cart_data),
        'total_amt': total_amt
    })

# Delete Cart Item
def delete_cart_item(request):
    p_id = str(request.GET['id'])
    cart_data = request.session.get('cartdata', {})
    
    if p_id in cart_data:
        del cart_data[p_id]
        request.session['cartdata'] = cart_data
    
    total_amt = sum(int(item['qty']) * float(item['price']) for item in cart_data.values())
    t = render_to_string('ajax/cart-list.html', {'cart_data': cart_data, 'totalitems': len(cart_data), 'total_amt': total_amt})
    return JsonResponse({'data': t, 'totalitems': len(cart_data)})

# Update Cart Item
def update_cart_item(request):
    p_id = str(request.GET['id'])
    p_qty = request.GET['qty']
    cart_data = request.session.get('cartdata', {})
    
    if p_id in cart_data:
        cart_data[p_id]['qty'] = p_qty
        request.session['cartdata'] = cart_data
    
    total_amt = sum(int(item['qty']) * float(item['price']) for item in cart_data.values())
    t = render_to_string('ajax/cart-list.html', {'cart_data': cart_data, 'totalitems': len(cart_data), 'total_amt': total_amt})
    return JsonResponse({'data': t, 'totalitems': len(cart_data)})
    
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            phone_number = form.cleaned_data.get('phone_number')
            # Create a UserAddressBook entry with the phone number
            UserAddressBook.objects.create(user=user, phone_number=phone_number, address='', status=False)
            username = form.cleaned_data.get('username')
            pwd = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=pwd)
            login(request, user)
            return redirect('home')
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})

@login_required
@csrf_exempt
def checkout(request):
    total_amt = 0
    totalAmt = 0
    order = CartOrder.objects.filter(user=request.user).last()

    # Check if the request is to clear the cart
    if request.method == "POST" and 'clear_cart' in request.POST:
        # Clear the cart for the logged-in user
        request.session['cartdata'] = {}
        return redirect('my_orders')  # Redirect to another page after clearing the cart
    
    # WhatsApp Button Data
    try:
        # Fetch the User instance for "Jonathan"
        user = User.objects.get(username="Jonathan")
        # Retrieve UserAddressBook entry for this user
        address_book_entry = UserAddressBook.objects.get(user=user)
        phone_number = address_book_entry.phone_number
    except (User.DoesNotExist, UserAddressBook.DoesNotExist):
        phone_number = None
    
    # Build the message template dynamically
    if order:
        cart_items = CartOrderItems.objects.filter(order=order)
        item_details = []
        
        for item in cart_items:
            item_details.append(f"{item.item} x {item.qty}")
        
        item_details_str = "\n".join(item_details)
        dynamic_message = f"Hi, I wanted to enquire about the following products from your online catalog:\n\n{item_details_str}"
    else:
        dynamic_message = "I'd like to make an enquiry."
    
    if phone_number:
        # Prepare WhatsApp URL
        whatsapp_url = f"https://wa.me/{phone_number}?text={dynamic_message.replace(' ', '%20').replace('\n', '%0A')}"
    else:
        whatsapp_url = None


    # Handle GET request for checkout page rendering
    if 'cartdata' in request.session:
        for p_id, item in request.session['cartdata'].items():
            totalAmt += int(item['qty']) * float(item['price'])

        # Automatically get the user's latest location
        latest_location = Location.objects.filter(user=request.user).last()

        # Create an order and associate it with the user's latest location
        order = CartOrder.objects.create(
            user=request.user,
            total_amt=totalAmt,
            location=latest_location  # Automatically set the latest location
        )

        # Create order items
        for p_id, item in request.session['cartdata'].items():
            total_amt += int(item['qty']) * float(item['price'])
            CartOrderItems.objects.create(
                order=order,
                invoice_no='INV-' + str(order.id),
                item=item['title'],
                image=item['image'],
                qty=item['qty'],
                price=item['price'],
                total=float(item['qty']) * float(item['price'])
            )

        # Process Payment
        host = request.get_host()
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': total_amt,
            'item_name': 'OrderNo-' + str(order.id),
            'invoice': 'INV-' + str(order.id),
            'currency_code': 'USD',
            'notify_url': 'http://{}{}'.format(host, reverse('paypal-ipn')),
            'return_url': 'http://{}{}'.format(host, reverse('payment_done')),
            'cancel_return': 'http://{}{}'.format(host, reverse('payment_cancelled')),
        }
        form = PayPalPaymentsForm(initial=paypal_dict)

        # Fetch the address
        address = UserAddressBook.objects.filter(user=request.user, status=True).first()

        # Fetch all locations for the user (optional if needed in template)
        locations = Location.objects.filter(user=request.user)

        return render(request, 'checkout.html', {
            'cart_data': request.session['cartdata'],
            'totalitems': len(request.session['cartdata']),
            'total_amt': total_amt,
            'form': form,
            'address': address,
            'whatsapp_url': whatsapp_url,
            'locations': locations  # Pass locations to the template
        })
    
    # If no cart data is found
    return redirect('some_error_page')  # Or handle the case as needed
                
@csrf_exempt
def payment_done(request):
	returnData=request.POST
	return render(request, 'payment-success.html',{'data':returnData})


@csrf_exempt
def payment_canceled(request):
	return render(request, 'payment-fail.html')


# Save Review
def save_review(request,pid):
	product=Product.objects.get(pk=pid)
	user=request.user
	review=ProductReview.objects.create(
		user=user,
		product=product,
		review_text=request.POST['review_text'],
		review_rating=request.POST['review_rating'],
		)
	data={
		'user':user.username,
		'review_text':request.POST['review_text'],
		'review_rating':request.POST['review_rating']
	}

	# Fetch avg rating for reviews
	avg_reviews=ProductReview.objects.filter(product=product).aggregate(avg_rating=Avg('review_rating'))
	# End

	return JsonResponse({'bool':True,'data':data,'avg_reviews':avg_reviews})

# User Dashboard
import calendar
def my_dashboard(request):
	orders=CartOrder.objects.annotate(month=ExtractMonth('order_dt')).values('month').annotate(count=Count('id')).values('month','count')
	monthNumber=[]
	totalOrders=[]
	for d in orders:
		monthNumber.append(calendar.month_name[d['month']])
		totalOrders.append(d['count'])
	return render(request, 'user/dashboard.html',{'monthNumber':monthNumber,'totalOrders':totalOrders})

# My Orders
def my_orders(request):
	orders=CartOrder.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/orders.html',{'orders':orders})

# Order Detail
def my_order_items(request,id):
	order=CartOrder.objects.get(pk=id)
	orderitems=CartOrderItems.objects.filter(order=order).order_by('-id')
	return render(request, 'user/order-items.html',{'orderitems':orderitems})

# Wishlist
def add_wishlist(request):
	pid=request.GET['product']
	product=Product.objects.get(pk=pid)
	data={}
	checkw=Wishlist.objects.filter(product=product,user=request.user).count()
	if checkw > 0:
		data={
			'bool':False
		}
	else:
		wishlist=Wishlist.objects.create(
			product=product,
			user=request.user
		)
		data={
			'bool':True
		}
	return JsonResponse(data)

# My Wishlist
def my_wishlist(request):
	wlist=Wishlist.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/wishlist.html',{'wlist':wlist})

# My Reviews
def my_reviews(request):
	reviews=ProductReview.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/reviews.html',{'reviews':reviews})

# My AddressBook
def my_addressbook(request):
	addbook=UserAddressBook.objects.filter(user=request.user).order_by('-id')
	return render(request, 'user/addressbook.html',{'addbook':addbook})

# Save addressbook
def save_address(request):
	msg=None
	if request.method=='POST':
		form=AddressBookForm(request.POST)
		if form.is_valid():
			saveForm=form.save(commit=False)
			saveForm.user=request.user
			if 'status' in request.POST:
				UserAddressBook.objects.update(status=False)
			saveForm.save()
			msg='Data has been saved'
	form=AddressBookForm
	return render(request, 'user/add-address.html',{'form':form,'msg':msg})

# Activate address
def activate_address(request):
	a_id=str(request.GET['id'])
	UserAddressBook.objects.update(status=False)
	UserAddressBook.objects.filter(id=a_id).update(status=True)
	return JsonResponse({'bool':True})

# Edit Profile
def edit_profile(request):
	msg=None
	if request.method=='POST':
		form=ProfileForm(request.POST,instance=request.user)
		if form.is_valid():
			form.save()
			msg='Data has been saved'
	form=ProfileForm(instance=request.user)
	return render(request, 'user/edit-profile.html',{'form':form,'msg':msg})

# Update addressbook
def update_address(request,id):
	address=UserAddressBook.objects.get(pk=id)
	msg=None
	if request.method=='POST':
		form=AddressBookForm(request.POST,instance=address)
		if form.is_valid():
			saveForm=form.save(commit=False)
			saveForm.user=request.user
			if 'status' in request.POST:
				UserAddressBook.objects.update(status=False)
			saveForm.save()
			msg='Data has been saved'
	form=AddressBookForm(instance=address)
	return render(request, 'user/update-address.html',{'form':form,'msg':msg})