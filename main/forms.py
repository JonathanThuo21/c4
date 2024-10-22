from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm,UserChangeForm,AuthenticationForm
from .models import ProductReview,UserAddressBook
from .models import CartOrder, CartOrderItems, UserAddressBook



class CartOrderForm(forms.ModelForm):
    class Meta:
        model = CartOrder
        fields = ['total_amt', 'paid_status', 'order_status', 'location']

class CartOrderItemsForm(forms.ModelForm):
    class Meta:
        model = CartOrderItems
        fields = ['invoice_no', 'item', 'image', 'qty', 'price', 'total']

class UserAddressBookForm(forms.ModelForm):
    class Meta:
        model = UserAddressBook
        fields = ['phone_number', 'address', 'status']


class SignupForm(UserCreationForm):
    phone_number = forms.CharField(max_length=13, required=True, help_text="Phone number must start with +254")
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone_number', 'password1', 'password2')

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if not phone_number.startswith("+254"):
            raise forms.ValidationError("Phone number must start with +254.")
        return phone_number

class PhoneLoginForm(AuthenticationForm):
    phone_number = forms.CharField(label='Phone Number', max_length=50)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    def clean(self):
        phone_number = self.cleaned_data.get('phone_number')
        password = self.cleaned_data.get('password')

        # Validate phone number and password
        if not phone_number or not password:
            raise forms.ValidationError("Phone number and password are required.")

        # Ensure that the phone number is associated with a user
        if not User.objects.filter(useraddressbook__mobile=phone_number).exists():
            raise forms.ValidationError("No user is associated with this phone number.")

        return super().clean()
    
# Review Add Form
class ReviewAdd(forms.ModelForm):
	class Meta:
		model=ProductReview
		fields=('review_text','review_rating')

# AddressBook Add Form
class AddressBookForm(forms.ModelForm):
	class Meta:
		model=UserAddressBook
		fields=['phone_number', 'address', 'status']

# ProfileEdit
class ProfileForm(UserChangeForm):
    password = forms.CharField(widget=forms.PasswordInput(), required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username', 'password')

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user