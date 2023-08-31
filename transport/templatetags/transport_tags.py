import decimal

from django import template
from django.contrib.sites import requests
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404


from transport.forms import *
from transport.models import *
from transport.views import menu

register = template.Library()


@register.filter(name="has_group")
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.inclusion_tag('transport/tags/load_list.html', takes_context=True)
def show_load(context, sort=None):
    user_filter = context.get('user', None)

    if has_group(user_filter, 'Admin'):
        if not sort:
            loads = Load.objects.all()
        else:
            loads = Load.objects.all().order_by('stat',
                                                'load_buy_price',
                                                'load_sell_price')
    elif has_group(user_filter, 'Support'):
        group_manager = User.objects.filter(groups__name='Manager')
        if not sort:
            loads = Load.objects.filter(user__id__in=group_manager)
        else:
            loads = Load.objects.filter(user__id__in=group_manager).order_by('stat',
                                                                             'load_buy_price',
                                                                             'load_sell_price')
    else:
        if not sort:
            loads = Load.objects.filter(user=user_filter)
        else:
            loads = Load.objects.filter(user=user_filter).order_by('stat',
                                                                   'load_buy_price',
                                                                   'load_sell_price')

    return {"loads": loads,
            }


@register.inclusion_tag('transport/tags/menu.html', takes_context=True)
def show_menu(context):
    return {'menu': menu,
            'user': context.get('user', None),
            'perms': context.get('perms', None),
            }


@transaction.atomic
@register.inclusion_tag('transport/tags/show_load_info.html', takes_context=True)
def show_load_info(context):
    load_slug = context.get('load_slug', None)
    load = get_object_or_404(Load, slug=load_slug)
    seller_load = SellerLoad.objects.filter(slug=load_slug)
    seller_load_form = AddSellerLoadForm(initial={'slug': load_slug})

    context = {
        'load': load,
        'seller_load': seller_load,
        'seller_load_form': seller_load_form,
        'title_add': 'Add new seller load',
        'title': f"Seller info - {load.load_prefix_broker}{load_slug}",
        'user': context.get('user', None),
        'perms': context.get('perms', None),
    }
    return context


@transaction.atomic
@register.inclusion_tag('transport/tags/show_seller_doc.html', takes_context=True)
def show_seller_doc(context, doc_slug):
    seller_doc = DocSeller.objects.filter(slug=doc_slug)
    seller_doc_form = AddDocSellerForm(initial={'slug': doc_slug})
    instance_load = get_object_or_404(SellerLoad, pk=doc_slug)
    if instance_load.seller_load_number == 'no info':
        instance_load.seller_load_number = ''
        instance_load.load_buy_price = 0
    if instance_load.pickup_location == 'no info' or instance_load.pickup_instructions == 'no info':
        instance_load.pickup_data = ''
        instance_load.pickup_time_from = ''
        instance_load.pickup_time_to = ''
        instance_load.pickup_location = ''
        instance_load.pickup_instructions = ''
    if instance_load.destination_location == 'no info' or instance_load.destination_instructions == 'no info':
        instance_load.destination_data = ''
        instance_load.destination_time_from = ''
        instance_load.destination_time_to = ''
        instance_load.destination_location = ''
        instance_load.destination_instructions = ''

    seller_load_edit = AddSellerLoadForm(instance=instance_load)

    cash_transaction_get = CashTransaction.objects.filter(buyer_seller='seller', counterparty=doc_slug,
                                                          transaction_name=1,).aggregate(cash_sum=Sum('cash_sum'))
    cash_transaction_get = cash_transaction_get['cash_sum']

    seller_debt = instance_load.load_buy_price
    if type(cash_transaction_get) == decimal.Decimal:
        cash_sum_get = cash_transaction_get
    else:
        cash_sum_get = 0

    cash_sum = seller_debt - cash_sum_get
    if cash_sum < 0:
        cash_sum = 0

    payment_form = CashTransactionForm(initial={
        'transaction_name': 1,
        'cash_sum': cash_sum,
    })

    transaction_get = CashTransaction.objects.filter(buyer_seller='seller', counterparty=doc_slug, transaction_name=1)
    transaction_send = CashTransaction.objects.filter(buyer_seller='seller', counterparty=doc_slug, transaction_name=2)
    transaction_all = CashTransaction.objects.filter(buyer_seller='seller', counterparty=doc_slug)
    context = {
        'seller_more': 'more ...',
        'load_slug': doc_slug,
        'transaction_all': transaction_all,
        'cash_sum': cash_sum,
        'transaction_send': transaction_send,
        'transaction_get': transaction_get,
        'payment_form': payment_form,
        'seller_doc': seller_doc,
        'seller_doc_form': seller_doc_form,
        'seller_load_edit': seller_load_edit,
        'doc_slug': doc_slug,
        's_load_id': doc_slug,
        'title': 'Documents:',
        'title_add_doc': 'Documents add and del',
        'title_edit_seller_load': 'Edit seller load',
        'title_button_save': 'Change seller load',
        'title_pay': 'Payment:',
        'title_payment': 'Payment add and del',
        'title_transaction': 'Add transaction',
        'user': context.get('user', None),
        'perms': context.get('perms', None),
        'load': context.get('load', None),
    }
    return context


@transaction.atomic
@register.inclusion_tag('transport/tags/buyer_load_info.html', takes_context=True)
def buyer_load_info(context):
    load_slug = context.get('load_slug', None)
    buyer_doc = DocBuyer.objects.filter(slug=load_slug)
    buyer_form = BuyerForm(initial={'slug': load_slug})
    buyer_doc_form = AddDocBuyerForm(initial={'slug': load_slug})
    buyer_doc_form_add = DocBuyerForm()
    try:
        buyer_load = BuyerLoad.objects.get(slug=load_slug)
        buyer_pk = buyer_load.pk
        buyer_credit = buyer_load.load_sell_price
        buyer_edit_form = BuyerForm(instance=buyer_load)
        title = 'Edit Buyer'

        cash_transaction_send = CashTransaction.objects.filter(buyer_seller='buyer', counterparty=buyer_load.pk,
                                                               transaction_name=2).aggregate(cash_sum=Sum('cash_sum'))
        cash_transaction_send = cash_transaction_send['cash_sum']

        if type(cash_transaction_send) == decimal.Decimal:
            cash_sum_send = cash_transaction_send
        else:
            cash_sum_send = 0

        cash_sum = buyer_credit - cash_sum_send
        if cash_sum < 0:
            cash_sum = 0

        payment_form = CashTransactionForm(initial={
            'slug': load_slug,
            'buyer_seller': 'buyer',
            'transaction_name': 2,
            'counterparty': buyer_load.pk,
            'cash_sum': cash_sum,
        })

        transaction_get = CashTransaction.objects.filter(buyer_seller='buyer', counterparty=buyer_load.pk,
                                                         transaction_name=1)
        transaction_send = CashTransaction.objects.filter(buyer_seller='buyer', counterparty=buyer_load.pk,
                                                          transaction_name=2)
        transaction_all = CashTransaction.objects.filter(buyer_seller='buyer', counterparty=buyer_load.pk)

    except BuyerLoad.DoesNotExist:
        buyer_pk = None
        payment_form = None
        transaction_all = None
        transaction_send = None
        transaction_get = None
        cash_sum = 0
        buyer_load = None
        buyer_edit_form = ''
        title = 'Add Buyer'

    load = Load.objects.get(slug=load_slug)
    try:
        load_stat = getattr(load, 'stat')
        if "created" != str(load_stat):
            load_stat = True
        else:
            load_stat = False
    except:
        load_stat = False

    context = {
        'load': load,
        'buyer_more': 'more ...',
        'buyer_pk': buyer_pk,
        'buyer_doc_form_add': buyer_doc_form_add,
        'transaction_all': transaction_all,
        'transaction_send': transaction_send,
        'transaction_get': transaction_get,
        'cash_sum': cash_sum,
        'payment_form': payment_form,
        'title_transaction': 'Add transaction',
        'title_payment': 'Payment add and del',
        'title_pay': 'Payment buyer:',
        'load_stat': load_stat,
        'buyer_edit_form': buyer_edit_form,
        'buyer_doc_form': buyer_doc_form,
        'buyer_doc': buyer_doc,
        'buyer_form': buyer_form,
        'buyer_load': buyer_load,
        'title': f'Buyer info - {load.load_prefix_broker}{load.slug}',
        'title_b_e': title,
        'title_add_doc': 'Documents add and del',
        'title_money': 'Money',
        'user': context.get('user', None),
        'perms': context.get('perms', None),
    }
    return context


@transaction.atomic
@register.inclusion_tag('transport/tags/seller_documents.html')
def seller_documents(load_slug):
    doc = DocSeller.objects.filter(slug=load_slug)
    doc_form = AddDocSellerForm(initial={'slug': load_slug})
    if doc:
        title = 'Seller documents'
    else:
        title = 'This seller has no documents'
    context = {
        'doc': doc,
        'doc_form': doc_form,
        'title': title,
        'title_add': 'Add seller document',
        'title_add_': 'Add doc',
    }
    return context


@transaction.atomic
@register.inclusion_tag('transport/tags/buyer_documents.html')
def buyer_documents(load_slug):
    doc = DocSeller.objects.filter(slug=load_slug)
    try:
        buyer_load = BuyerLoad.objects.get(slug=load_slug)
    except BuyerLoad.DoesNotExist:
        buyer_load = None

    doc_buyer = DocBuyer.objects.filter(slug=load_slug)
    doc_form = AddDocBuyerForm(initial={'slug': load_slug})
    if doc_buyer:
        title = 'Buyer documents'
    else:
        title = 'This seller has no documents'
    context = {
        'doc': doc,
        'buyer_load': buyer_load,
        'doc_buyer': doc_buyer,
        'doc_form': doc_form,
        'title': title,
        'title_add': 'Add buyer document',
        'title_add_': 'Add doc',
    }
    return context


@transaction.atomic
@register.inclusion_tag('transport/tags/load_info.html', takes_context=True)
def load_info(context):
    load_slug = context.get('load_slug', None)
    try:
        load_data = get_object_or_404(Load, slug=load_slug)

        company_broker_load = get_object_or_404(Company, company_mc=load_data.load_broker)
        company_carrier_load = get_object_or_404(Company, company_mc=load_data.load_carrier)

        seller_payment_get = CashTransaction.objects.filter(slug=load_data, buyer_seller='seller',
                                                            executed=True, transaction_name=1).\
            aggregate(cash_sum=Sum('cash_sum'))
        seller_payment_get = seller_payment_get['cash_sum']
        seller_payment_send = CashTransaction.objects.filter(slug=load_data, buyer_seller='seller', executed=True,
                                                             transaction_name=2).aggregate(cash_sum=Sum('cash_sum'))
        seller_payment_send = seller_payment_send['cash_sum']

        buyer_payment_get = CashTransaction.objects.filter(slug=load_data, buyer_seller='buyer', executed=True,
                                                           transaction_name=1).aggregate(cash_sum=Sum('cash_sum'))
        buyer_payment_get = buyer_payment_get['cash_sum']
        buyer_payment_send = CashTransaction.objects.filter(slug=load_data, buyer_seller='buyer', executed=True,
                                                            transaction_name=2).aggregate(cash_sum=Sum('cash_sum'))
        buyer_payment_send = buyer_payment_send['cash_sum']

        seller_payment_all = CashTransaction.objects.filter(slug=load_data, buyer_seller='seller', )
        buyer_payment_all = CashTransaction.objects.filter(slug=load_data, buyer_seller='buyer', )

        form_load = SetDefaultCompanyForm(initial={'company_broker_default': company_broker_load.pk,
                                                   'company_carrier_default': company_carrier_load.pk})

    except BuyerLoad.DoesNotExist:
        seller_payment_all = None
        buyer_payment_all = None
        seller_payment_send = 0
        seller_payment_get = 0
        buyer_payment_send = 0
        buyer_payment_get = 0

    if seller_payment_get is None:
        seller_payment_get = 0
    if seller_payment_send is None:
        seller_payment_send = 0
    seller_debt = seller_payment_get - seller_payment_send

    if buyer_payment_get is None:
        buyer_payment_get = 0
    if buyer_payment_send is None:
        buyer_payment_send = 0
    buyer_credit = buyer_payment_send - buyer_payment_get

    profit = seller_debt - buyer_credit

    exists_transaction_load = CashTransaction.objects.filter(slug=load_slug).exists()

    user_choice = UserChoiceForm(initial={'user_name': load_data.user})
    status_choice = SetStatus()

    context = {
        'status_choice': status_choice,
        'button_set_status': 'Set status',
        'user_choice': user_choice,
        'button_set_user': 'Set user',
        'exists_transaction_load': exists_transaction_load,
        'load_data': load_data,
        'form_load': form_load,
        'company_broker_load': company_broker_load,
        'company_carrier_load': company_carrier_load,
        'seller_payment_all': seller_payment_all,
        'buyer_payment_all': buyer_payment_all,
        'seller_debt': seller_debt,
        'buyer_credit': buyer_credit,
        'profit': profit,
        'title_load': f'Load info - {load_data.load_prefix_broker}{load_slug} - {load_data.stat}',
        'load_slug': load_slug,
        'title_button': 'more ...',
        'button_set_seller_and_carrier': 'Set Broker and Carrier',
        'user': context.get('user', None),
        'perms': context.get('perms', None),
    }
    return context
