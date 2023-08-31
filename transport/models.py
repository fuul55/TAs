import os
from time import strftime

from django.contrib.auth.models import User
from django.db import models
from django.db.models import EmailField, TimeField
from django.urls import reverse
from django.utils.crypto import get_random_string


class GenNumLoad(models.Model):
    def __str__(self):
        return self.pk


def generation_number():
    new = GenNumLoad.objects.create()
    number_of_zeros = 6
    counter = 0
    zeros = ""
    y = 0
    for i in str(new.id):
        counter += 1
    while y < number_of_zeros - counter:
        y += 1
        zeros += "0"
    num = zeros + str(new.id)

    return num


def get_file_path(instance, filename):
    ext = filename.split('.')[-1]
    if Load.objects.all().exists():
        load = Load.objects.all().order_by('-id')[0]
    else:
        load = '1'
    unique_id = get_random_string(length=6) + str(load) + get_random_string(length=6)
    filename = "%s.%s" % (unique_id, ext)
    return os.path.join(instance.directory_string_var, filename)


class CompanyTypeName(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name="Status")

    def __str__(self):
        return self.name


class Company(models.Model):
    company_mc = models.CharField(unique=True, max_length=7, verbose_name="Company MC")
    company_dot = models.CharField(max_length=7, verbose_name="Company DOT")
    company_name = models.CharField(max_length=255, verbose_name="Company name")
    company_address = models.CharField(max_length=255, verbose_name="Company address")
    company_type = models.ForeignKey('CompanyTypeName', on_delete=models.PROTECT, verbose_name="Company type")
    company_email = EmailField(max_length=254, blank=True, verbose_name="Company Email")
    company_phone = models.CharField(max_length=20, blank=True, verbose_name="Company phone")
    company_prefix = models.CharField(blank=True, max_length=3, verbose_name="Company prefix")
    company_default = models.CharField(max_length=7, blank=True, verbose_name="Default Company")
    company_wire = models.TextField(blank=True, verbose_name="Wire instructions")
    part_holding = models.BooleanField(default=False, verbose_name="Part holding")
    company_logo = models.FileField(upload_to=get_file_path, blank=True,
                                    verbose_name="Company logo")
    directory_string_var = "logo/company/"

    def __str__(self):
        return str(self.company_mc)

    def get_absolute_url(self):
        return reverse('show_company', kwargs={'pk': self.pk})

    def delete(self, *args, **kwargs):
        if self.company_logo:
            # До удаления записи получаем необходимую информацию
            storage, path = self.company_logo.storage, self.company_logo.path
            # Удаляем сначала модель (объект)
            super(Company, self).delete(*args, **kwargs)
            # Потом удаляем сам файл
            storage.delete(path)


class Load(models.Model):
    slug = models.SlugField(unique=True, db_index=True, editable=True, verbose_name="Load number")
    load_buy_price = models.DecimalField(verbose_name="Load buy price", max_digits=19, decimal_places=2, default=0.00)
    load_sell_price = models.DecimalField(verbose_name="Load sell price", max_digits=19, decimal_places=2, default=0.00)
    load_profit = models.DecimalField(verbose_name="Load profit", max_digits=19, decimal_places=2, default=0.00)
    load_broker = models.ForeignKey('Company', blank=True, null=True, related_name='load_broker',
                                    on_delete=models.PROTECT, verbose_name="Broker MC")
    load_prefix_broker = models.CharField(max_length=3, verbose_name="Broker prefix")
    load_carrier = models.ForeignKey('Company', blank=True, null=True, related_name='load_carrier',
                                     on_delete=models.PROTECT, verbose_name="Carrier MC")
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, editable=True, verbose_name="User name")
    date_create = models.DateField(auto_now_add=True, editable=False, blank=True, verbose_name="Date create load")
    date_update = models.DateTimeField(auto_now=True, verbose_name="Load date update")
    stat = models.ForeignKey('Status', on_delete=models.PROTECT, default=2,
                             editable=True, verbose_name="Status")

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('load', kwargs={'load_slug': self.slug})

    class Meta:
        verbose_name = "Loads"
        verbose_name_plural = 'Load'
        ordering = ['-date_update']


class SellerLoad(models.Model):
    slug = models.SlugField(db_index=True, editable=True, verbose_name="Load number")
    seller_load_number = models.CharField(max_length=30, db_index=True, verbose_name="Seller load number")
    load_buy_price = models.DecimalField(verbose_name="Seller price", max_digits=19, decimal_places=2)
    pickup_data = models.DateField(auto_now_add=False, verbose_name="Pickup date")
    pickup_time_from = models.TimeField(verbose_name="Time from")
    pickup_time_to = models.TimeField(verbose_name="Time to")
    pickup_location = models.TextField(verbose_name="Pickup Location")
    pickup_instructions = models.TextField(verbose_name="Pickup Instructions")
    destination_data = models.DateField(auto_now_add=False, verbose_name="Destination date")
    destination_time_from = models.TimeField(verbose_name="Time from")
    destination_time_to = models.TimeField(verbose_name="Time to")
    destination_location = models.TextField(verbose_name="Destination Location")
    destination_instructions = models.TextField(verbose_name="Destination Instructions")
    company_mc = models.ForeignKey('Company', blank=True, null=True,
                                   on_delete=models.PROTECT, verbose_name="Company MC")
    seller_MC = models.CharField(max_length=7, verbose_name="Seller MC")
    date_create = models.DateTimeField(auto_now_add=True, verbose_name="Date create load")
    date_update = models.DateTimeField(auto_now=True, verbose_name="Date update load")

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('seller_load', kwargs={'seller_id': self.pk})


class DocSeller(models.Model):
    slug = models.SlugField(db_index=True, editable=True, blank=False, verbose_name="ID seller load")
    doc = models.ForeignKey('DocumentName', on_delete=models.PROTECT, verbose_name="Seller documents name")
    documents = models.FileField(upload_to=get_file_path,
                                 verbose_name="Seller document")

    directory_string_var = f"documents/seller/"

    def __str__(self):
        return str(self.slug)

    def delete(self, *args, **kwargs):
        # До удаления записи получаем необходимую информацию
        storage, path = self.documents.storage, self.documents.path
        # Удаляем сначала модель (объект)
        super(DocSeller, self).delete(*args, **kwargs)
        # Потом удаляем сам файл
        storage.delete(path)


class BuyerLoad(models.Model):
    slug = models.SlugField(unique=True, db_index=True, editable=True, verbose_name="Load number")
    truck_info = models.TextField(verbose_name="Truck info")
    truck_requirements = models.TextField(verbose_name="Load info")
    company_mc = models.ForeignKey('Company', blank=True, null=True,
                                   on_delete=models.PROTECT, verbose_name="Company MC")
    buyer_MC = models.CharField(max_length=7, verbose_name="Buyer MC")
    date_sold_load = models.DateField(auto_now_add=False, verbose_name="Sold date load")
    load_sell_price = models.DecimalField(verbose_name="Sell price", max_digits=19, decimal_places=2)
    date_create = models.DateTimeField(auto_now_add=True, verbose_name="Date create load")
    date_update = models.DateTimeField(auto_now=True, verbose_name="Date update load")

    def __str__(self):
        return self.slug


class DocBuyer(models.Model):
    slug = models.SlugField(db_index=True, editable=True, verbose_name="Load number")
    doc = models.ForeignKey('DocumentName', on_delete=models.PROTECT, verbose_name="Buyer document name")
    documents = models.FileField(upload_to=get_file_path,
                                 verbose_name="Buyer document")
    directory_string_var = "documents/buyer/"

    def __str__(self):
        return str(self.slug)

    def delete(self, *args, **kwargs):
        storage, path = self.documents.storage, self.documents.path
        super(DocBuyer, self).delete(*args, **kwargs)
        storage.delete(path)


class Status(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name="Status")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['id']


class DocumentName(models.Model):
    name = models.CharField(max_length=100, verbose_name="Document name")

    def __str__(self):
        return self.name


class Transaction(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name="Status")

    def __str__(self):
        return self.name


class CashTransaction(models.Model):
    slug = models.ForeignKey('Load', null=True, blank=True, on_delete=models.PROTECT,
                             verbose_name="Load number")
    broker_carrier_mc = models.ForeignKey('Company', on_delete=models.PROTECT, related_name='broker_carrier_mc',
                                          verbose_name="Broker / Carrier MC")
    buyer_seller_mc = models.ForeignKey('Company', on_delete=models.PROTECT, related_name='buyer_seller_mc',
                                        default=2, verbose_name="Buyer / Seller (holding)")
    buyer_seller = models.CharField(max_length=7, blank=True, verbose_name="buyer / seller")
    counterparty = models.CharField(max_length=255, blank=True, verbose_name="Counterparty")
    transaction_name = models.ForeignKey('Transaction', on_delete=models.PROTECT,
                                         editable=True, verbose_name="Transaction type")
    cash_sum = models.DecimalField(verbose_name="Amount", max_digits=19, decimal_places=2)
    transaction_data = models.DateField(auto_now_add=False, verbose_name="Transaction date")
    comment = models.TextField(blank=True, verbose_name="Purpose of payment")
    executed = models.BooleanField(default=False, verbose_name="Executed")
    payment_doc = models.FileField(upload_to=get_file_path,
                                   verbose_name="Payment doc")
    directory_string_var = "documents/payment_doc/"

    def __str__(self):
        return str(self.pk)

    def get_absolute_url(self):
        return reverse('show_info_pay', kwargs={'to_pay_id': self.pk})

    def delete(self, *args, **kwargs):
        storage, path = self.payment_doc.storage, self.payment_doc.path
        super(CashTransaction, self).delete(*args, **kwargs)
        storage.delete(path)


class UserCompany(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    user_company = models.ForeignKey('Company', on_delete=models.PROTECT,
                                     blank=True, null=True,
                                     related_name='Company_mc',
                                     verbose_name="Company for user")
    load_broker_default = models.ForeignKey('Company', on_delete=models.PROTECT,
                                            blank=True, null=True,
                                            related_name='Default_Broker_mc',
                                            verbose_name="Default Broker for user")
    load_carrier_default = models.ForeignKey('Company', on_delete=models.PROTECT,
                                             blank=True, null=True,
                                             related_name='Default_Carrier_mc',
                                             verbose_name="Default Carrier for user")