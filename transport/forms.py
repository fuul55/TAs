from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm, AuthenticationForm
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import *
from .util import MyDateInput


class QuikAddLoadForm(forms.Form):
    seller_MC = forms.CharField(max_length=7, label="Seller MC",
                                widget=forms.NumberInput(attrs={'class': 'form-input',
                                                                'autocomplete': 'off',
                                                                'pattern': '[0-9]+',
                                                                'max': '9999999',
                                                                'title': 'Enter numbers Only '}))


class SearchSellerForm(forms.Form):
    seller_MC = forms.CharField(max_length=7, label="Seller MC",
                                widget=forms.NumberInput(attrs={'class': 'form-input', 'max_value': '100'}))


class DataRangCompanyTransaction(forms.Form):
    data_from = forms.DateField(widget=MyDateInput(attrs={'class': 'form-input'}))
    data_to = forms.DateField(widget=MyDateInput(attrs={'class': 'form-input'}))


class AddSellerForm(forms.Form):
    seller_MC = forms.CharField(max_length=7, label="Seller MC",
                                widget=forms.TextInput(attrs={'class': 'form-input'}))
    seller_DOT = forms.CharField(max_length=7, label="Seller DOT",
                                 widget=forms.TextInput(attrs={'class': 'form-input'}))
    seller_name = forms.CharField(max_length=255, label="Seller name",
                                  widget=forms.TextInput(attrs={'class': 'form-input'}))
    seller_address = forms.CharField(max_length=255, label="Seller address",
                                     widget=forms.TextInput(attrs={'class': 'form-input'}))
    seller_email = forms.EmailField(max_length=100, label="Seller e-mail", required=False,
                                    widget=forms.EmailInput(attrs={'class': 'form-input'}))
    seller_phone = forms.CharField(max_length=100, label="Seller phone", required=False,
                                   widget=forms.TextInput(attrs={'class': 'form-input'}))


class SetDefaultCompanySettingForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_broker_default'].empty_label = "Select company"
        self.fields['company_broker_default'].label = "Broker default company name"
        self.fields['company_broker_default'].queryset = Company.objects.filter(company_type=1, part_holding=True)
        self.fields['company_broker_default'].label_from_instance = self.label_from_instance
        self.fields['company_carrier_default'].empty_label = "Select company"
        self.fields['company_carrier_default'].label = "Carrier default company name"
        self.fields['company_carrier_default'].queryset = Company.objects.filter(company_type=2, part_holding=True)
        self.fields['company_carrier_default'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(self):
        return str(self.company_name)

    company_broker_default = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=1,
                                                                                    part_holding=True),
                                                    widget=forms.Select(attrs={'class': 'form-input-select'}),
                                                    empty_label='Select broker company MC')
    company_carrier_default = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=2,
                                                                                     part_holding=True),
                                                     widget=forms.Select(attrs={'class': 'form-input-select'}),
                                                     empty_label='Select carrier company MC')


class SetStatus(forms.Form):
    GEEKS_CHOICES = (
        ("0", "Select status"),
        ("4", "Open the load"),
        ("1", "Close the load"),
        ("2", "Cancel the load"),
        # ("3", "SOS"),
    )
    status_load = forms.ChoiceField(choices=GEEKS_CHOICES,
                                    label='Load status',
                                    widget=forms.Select(attrs={'class': 'form-input-select'}))


class SetDefaultCompanyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_broker_default'].empty_label = "Select company"
        self.fields['company_broker_default'].label = "Broker default company name"
        self.fields['company_broker_default'].queryset = Company.objects.filter(company_type=1, part_holding=True)
        self.fields['company_broker_default'].label_from_instance = self.label_from_instance
        self.fields['company_carrier_default'].empty_label = "Select company"
        self.fields['company_carrier_default'].label = "Carrier default company name"
        self.fields['company_carrier_default'].queryset = Company.objects.filter(company_type=2, part_holding=True)
        self.fields['company_carrier_default'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(self):
        return str(self.company_name)

    company_broker_default = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=1,
                                                                                    part_holding=True),
                                                    widget=forms.Select(attrs={'class': 'form-input-select'}),
                                                    empty_label='Select broker company MC')
    company_carrier_default = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=2,
                                                                                     part_holding=True),
                                                     widget=forms.Select(attrs={'class': 'form-input-select'}),
                                                     empty_label='Select carrier company MC')


class AddLoadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = Load
        fields = ['slug',
                  'load_buy_price',
                  'load_sell_price',
                  ]
        widgets = {
            'slug': forms.TextInput(attrs={'class': 'form-input-gray', 'readonly': True}),
            'load_buy_price': forms.NumberInput(attrs={'class': 'form-input'}),
            'load_sell_price': forms.NumberInput(attrs={'class': 'form-input'}),
        }


class AddSellerLoadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = SellerLoad
        fields = ['slug', 'seller_load_number', 'load_buy_price', 'pickup_data', 'pickup_time_from',
                  'pickup_time_to', 'pickup_location', 'pickup_instructions', 'destination_data',
                  'destination_time_from',
                  'destination_time_to', 'destination_location', 'destination_instructions', 'seller_MC',
                  'company_mc',

                  ]
        widgets = {
            'slug': forms.TextInput(attrs={'class': 'form-input-gray', 'readonly': True}),
            'seller_load_number': forms.TextInput(attrs={'class': 'form-input'}),
            'load_buy_price': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'pickup_data': MyDateInput(attrs={'class': 'form-input'}),
            'pickup_time_from': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'pickup_time_to': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'pickup_location': forms.Textarea(attrs={'class': 'form-input-area'}),
            'pickup_instructions': forms.Textarea(attrs={'class': 'form-input-area'}),
            'destination_data': MyDateInput(attrs={'class': 'form-input'}),
            'destination_time_from': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'destination_time_to': forms.TimeInput(attrs={'class': 'form-input', 'type': 'time'}),
            'destination_location': forms.Textarea(attrs={'class': 'form-input-area'}),
            'destination_instructions': forms.Textarea(attrs={'class': 'form-input-area'}),
            'seller_MC': forms.NumberInput(attrs={'class': 'form-input',
                                                  'pattern': '[0-9]+',
                                                  'max': '9999999',
                                                  'title': 'Enter numbers Only '}),
            'company_mc': forms.HiddenInput(),
        }


class DocSellerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doc'].empty_label = "Select documents type"

    class Meta:
        model = DocSeller
        fields = ['doc', 'documents']
        widgets = {
            'doc': forms.Select(attrs={'class': 'form-input-select'}),
        }


class AddDocSellerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doc'].empty_label = "Select documents type"

    class Meta:
        model = DocSeller
        fields = ['slug', 'doc', 'documents']
        widgets = {
            'slug': forms.TextInput(attrs={'class': 'form-input-gray', 'readonly': True}),
            'doc': forms.Select(attrs={'class': 'form-input-select'}),
        }


class BuyerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = BuyerLoad
        fields = ['slug', 'load_sell_price', 'date_sold_load', 'truck_info', 'truck_requirements', 'buyer_MC',
                  'company_mc',
                  ]
        widgets = {
            'slug': forms.TextInput(attrs={'class': 'form-input-gray', 'readonly': True}),
            'load_sell_price': forms.NumberInput(attrs={'class': 'form-input'}),
            'date_sold_load': MyDateInput(attrs={'class': 'form-input'}),
            'truck_info': forms.Textarea(attrs={'class': 'form-input-area',
                                                'placeholder': 'drivers name and phone number, truck/trailer number ...'}),
            'truck_requirements': forms.Textarea(attrs={
                'class': 'form-input-area', 'placeholder': 'distance, weight, trailer, ...'}),
            'company_mc': forms.HiddenInput(),
            'buyer_MC': forms.NumberInput(attrs={'class': 'form-input',
                                                 'pattern': '[0-9]+',
                                                 'max': '9999999',
                                                 'title': 'Enter numbers Only '}),
        }


class DocBuyerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['documents'].label = 'Buyer Rate Confirmation'

    class Meta:
        model = DocBuyer
        fields = ['documents']


class AddDocBuyerForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['doc'].empty_label = "Select documents type"

    class Meta:
        model = DocBuyer
        fields = ['slug', 'doc', 'documents']
        widgets = {
            'slug': forms.TextInput(attrs={'class': 'form-input-gray', 'readonly': True}),
            'doc': forms.Select(attrs={'class': 'form-input-select'}),
        }


class CashTransactionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_name'].empty_label = "Select transaction type"

    class Meta:
        model = CashTransaction
        fields = ['slug',
                  'broker_carrier_mc',
                  'buyer_seller_mc',
                  'buyer_seller',
                  'counterparty',
                  'transaction_name',
                  'cash_sum',
                  'transaction_data',
                  'comment',
                  'payment_doc',
                  ]
        widgets = {
            'slug': forms.HiddenInput(),
            'broker_carrier_mc': forms.HiddenInput(),
            'buyer_seller_mc': forms.HiddenInput(),
            'buyer_seller': forms.HiddenInput(),
            'counterparty': forms.HiddenInput(),
            'transaction_name': forms.Select(attrs={'class': 'form-input-select'}),
            'cash_sum': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'transaction_data': MyDateInput(attrs={'class': 'form-input'}),
            'comment': forms.Textarea(attrs={'class': 'form-input-area',
                                             'placeholder': 'description ...'}),
        }


class CashTransactionFinanceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    class Meta:
        model = CashTransaction
        fields = [
            'cash_sum',
            'transaction_data',
            'comment',
            'executed',

        ]
        widgets = {
            'cash_sum': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'transaction_data': MyDateInput(attrs={'class': 'form-input'}),
            'executed': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'comment': forms.Textarea(attrs={'class': 'form-input-area',
                                             'placeholder': 'description ...'}),
        }


class CashTransactionCompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['transaction_name'].empty_label = "Select transaction type"
        self.fields['buyer_seller_mc'].empty_label = "Select company"
        self.fields['buyer_seller_mc'].queryset = Company.objects.filter(part_holding=True)
        self.fields['buyer_seller_mc'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(self):
        return str(self.company_name)

    class Meta:
        model = CashTransaction
        fields = ['transaction_name',
                  'buyer_seller_mc',
                  'cash_sum',
                  'transaction_data',
                  'comment',
                  'executed',
                  'payment_doc',
                  'broker_carrier_mc',
                  'buyer_seller',
                  'counterparty',
                  ]
        widgets = {
            'broker_carrier_mc': forms.HiddenInput(),
            'buyer_seller': forms.HiddenInput(),
            'counterparty': forms.HiddenInput(),
            'buyer_seller_mc': forms.Select(attrs={'class': 'form-input-select'}),
            'transaction_name': forms.Select(attrs={'class': 'form-input-select'}),
            'cash_sum': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'transaction_data': MyDateInput(attrs={'class': 'form-input'}),
            'executed': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'comment': forms.Textarea(attrs={'class': 'form-input-area',
                                             'placeholder': 'description ...'}),
        }


class CashTransactionCompanyInvoiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['broker_carrier_mc'].empty_label = "Select company"
        self.fields['broker_carrier_mc'].label = "Company name"
        self.fields['broker_carrier_mc'].queryset = Company.objects.filter(part_holding=True)
        self.fields['broker_carrier_mc'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(self):
        return str(self.company_name)

    bill_to = forms.CharField(max_length=255, label="Bill to",
                              widget=forms.Textarea(attrs={'class': 'form-input-area',
                                                           'placeholder': 'bill info ...'}))
    description = forms.CharField(max_length=255, label="Description",
                                  widget=forms.Textarea(attrs={'class': 'form-input-area',
                                                               'placeholder': 'description ...'}))
    amount = forms.DecimalField(label="Amount",
                                widget=forms.NumberInput(attrs={'class': 'form-input', 'min': 1}))

    class Meta:
        model = CashTransaction
        fields = ['broker_carrier_mc',
                  ]
        widgets = {
            'broker_carrier_mc': forms.Select(attrs={'class': 'form-input-select'}),
        }


class CompanyForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_type'].empty_label = "Select company type"

    class Meta:
        model = Company
        fields = ['company_type', 'company_mc', 'company_email',
                  'company_phone', 'company_prefix', 'company_wire', 'company_logo']
        widgets = {
            'company_mc': forms.NumberInput(
                attrs={'class': 'form-input', 'pattern': '[0-9]+', 'max': '9999999', 'title': 'Enter numbers Only '}),
            # 'company_dot': forms.TextInput(attrs={'class': 'form-input'}),
            # 'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            # 'company_address': forms.TextInput(attrs={'class': 'form-input'}),
            'company_type': forms.Select(attrs={'class': 'form-input-select'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'company_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'company_prefix': forms.TextInput(attrs={'class': 'form-input'}),
            'company_wire': forms.Textarea(attrs={'class': 'form-input-area',
                                                  'placeholder': 'displayed in the Invoice or Rate Confirmation'}),
        }


class CompanyFullForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company_type'].empty_label = "Select company type"
        self.fields['company_logo'].widget.initial_text = ""
        self.fields['company_logo'].widget.input_text = ""

    class Meta:
        model = Company
        fields = ['company_type', 'company_mc', 'company_dot', 'company_name', 'company_address', 'company_email',
                  'company_phone', 'company_prefix', 'company_wire', 'company_logo', 'part_holding']
        widgets = {
            'company_mc': forms.NumberInput(
                attrs={'class': 'form-input',
                       'pattern': '[0-9]+',
                       'max': '9999999',
                       'title': 'Enter numbers Only ',
                       'readonly': False}),
            'company_dot': forms.TextInput(attrs={'class': 'form-input'}),
            'company_name': forms.TextInput(attrs={'class': 'form-input'}),
            'company_address': forms.TextInput(attrs={'class': 'form-input'}),
            'company_type': forms.Select(attrs={'class': 'form-input-select'}),
            'company_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'company_phone': forms.TextInput(attrs={'class': 'form-input'}),
            'company_prefix': forms.TextInput(attrs={'class': 'form-input'}),
            'company_wire': forms.Textarea(attrs={'class': 'form-input-area',
                                                  'placeholder': 'displayed in the Invoice or Rate Confirmation'}),
            'part_holding': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'company_logo': forms.ClearableFileInput(attrs={'class': 'form-input'}),
        }


class RegisterUserForm(UserCreationForm):
    last_name = forms.CharField(label='Last name', widget=forms.TextInput(attrs={'class': 'form-input'}))
    first_name = forms.CharField(label='First name', widget=forms.TextInput(attrs={'class': 'form-input'}))
    username = forms.CharField(label='Username', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    email = forms.EmailField(label='Email', widget=forms.EmailInput(attrs={'class': 'form-input'}))
    is_active = forms.BooleanField(label='Active',
                                   required=False,
                                   widget=forms.CheckboxInput(attrs={'class': 'custom-checkbox'}))

    class Meta:
        model = User
        fields = ('username',
                  'password1',
                  'password2',
                  'first_name',
                  'last_name',
                  'is_superuser',
                  'is_staff',
                  'email',
                  'groups',
                  'is_active'
                  )
        widgets = {
            'is_superuser': forms.HiddenInput(),
            'is_staff': forms.HiddenInput(),
            'groups': forms.SelectMultiple(attrs={'class': 'form-input-multi'})
        }


class EditUserForm(SetPasswordForm):
    new_password1 = forms.CharField(min_length=8, label='New password',
                                    widget=forms.PasswordInput(attrs={'class': 'form-input',
                                                                      'pattern': '^(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$'}))
    new_password2 = forms.CharField(label='New password confirmation',
                                    widget=forms.PasswordInput(attrs={'class': 'form-input',
                                                                      'pattern': '^(?=^.{8,}$)((?=.*\d)|(?=.*\W+))(?![.\n])(?=.*[A-Z])(?=.*[a-z]).*$'}))


class ChangeUserForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_company'].empty_label = "Select broker company"
        self.fields['user_company'].label = "User company name"
        self.fields['user_company'].queryset = Company.objects.filter(company_type=1, part_holding=True)
        self.fields['user_company'].label_from_instance = self.label_from_instance
        self.fields['load_broker_default'].empty_label = "Select broker company"
        self.fields['load_broker_default'].label = "Default broker company name"
        self.fields['load_broker_default'].queryset = Company.objects.filter(company_type=1, part_holding=True)
        self.fields['load_broker_default'].label_from_instance = self.label_from_instance
        self.fields['load_carrier_default'].empty_label = "Select carrier company"
        self.fields['load_carrier_default'].label = "Default carrier company name"
        self.fields['load_carrier_default'].queryset = Company.objects.filter(company_type=2, part_holding=True)
        self.fields['load_carrier_default'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(self):
        return str(self.company_name)

    password = None

    user_company = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=1, part_holding=True),
                                          required=False,
                                          widget=forms.Select(attrs={'class': 'form-input-select'}),
                                          empty_label='Select broker company MC')
    load_broker_default = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=1, part_holding=True),
                                                 required=False,
                                                 widget=forms.Select(attrs={'class': 'form-input-select'}),
                                                 empty_label='Select default broker company MC')
    load_carrier_default = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=2, part_holding=True),
                                                  required=False,
                                                  widget=forms.Select(attrs={'class': 'form-input-select'}),
                                                  empty_label='Select default carrier company MC')

    class Meta:
        model = User
        fields = (
                  'first_name',
                  'last_name',
                  'email',
                  'groups',
                  'is_active',
                  )
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'custom-checkbox'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-input-multi'})
        }


class LoginUserForm(AuthenticationForm):
    username = forms.CharField(label='Login', widget=forms.TextInput(attrs={'class': 'form-input'}))
    password = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class UserChoiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user_name'].empty_label = "Select User"
        self.fields['user_name'].label = "User name"
        group = Group.objects.filter(name__in=['Admin', 'Manager', 'Super Manager'])
        self.fields['user_name'].queryset = User.objects.filter(groups__in=group, is_active=True, is_staff=False,)

    @staticmethod
    def label_from_instance(self):
        return str(self.username)

    user_name = forms.ModelChoiceField(queryset=Company.objects.filter(company_type=1, part_holding=True),
                                       required=False,
                                       widget=forms.Select(attrs={'class': 'form-input-select'}),
                                       empty_label='Select User',
                                       )
