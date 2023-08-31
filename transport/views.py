import copy
import decimal
import datetime

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import LoginView
from django.db import transaction
from django.db.models import Sum
from django.http import HttpResponseNotFound, HttpResponseRedirect
from django.middleware.csrf import CsrfViewMiddleware
from django.shortcuts import render, redirect, get_object_or_404
from django.template.defaulttags import csrf_token
from django.views.decorators.cache import cache_control
from pyexpat.errors import messages

from .forms import *
from .models import *

from .util import get_mc_info

menu = [{'title': 'Add load', 'url_name': 'add_doc', 'img': "/static/transport/images/add_load.svg"},
        {'title': 'My tasks', 'url_name': 'mytask', 'img': "/static/transport/images/tD.svg"},
        {'title': "Load list", 'url_name': 'load_list', 'img': "/static/transport/images/load.svg"},
        {'title': "Finance", 'url_name': 'finance', 'img': "/static/transport/images/fin.svg"},
        {'title': 'Setting', 'url_name': 'setting', 'img': "/static/transport/images/settings_grey.svg"},
        {'title': 'User authorization', 'url_name': 'logout', 'img': "/static/transport/images/logout.svg"},
        ]


def index(request):
    context = {
        'title': 'Transportation accounting system',
    }
    if request.user.is_authenticated:
        return render(request, 'transport/index.html', context=context)
    else:
        return redirect('login_u')


def status_load(load_slug):
    if BuyerLoad.objects.filter(slug=load_slug).exists() and \
            CashTransaction.objects.filter(slug=load_slug).exists():
        stat_load = 5
    elif BuyerLoad.objects.filter(slug=load_slug).exists():
        stat_load = 4
    else:
        stat_load = 3
    return stat_load


@transaction.atomic
def get_sent_profit(load_slug):
    load = get_object_or_404(Load, slug=load_slug)

    if CashTransaction.objects.filter(slug=load).exists():
        Load.objects.filter(slug=load_slug).update(load_buy_price=0, load_sell_price=0)

        company_transactions_buyer_get = CashTransaction.objects.filter(
            slug=load, buyer_seller='buyer', transaction_name=1, executed=True).aggregate(Sum('cash_sum'))
        company_transactions_buyer_send = CashTransaction.objects.filter(
            slug=load, buyer_seller='buyer', transaction_name=2, executed=True).aggregate(Sum('cash_sum'))
        if company_transactions_buyer_get['cash_sum__sum']:
            company_transactions_buyer_get = company_transactions_buyer_get['cash_sum__sum']
        else:
            company_transactions_buyer_get = 0
        if company_transactions_buyer_send['cash_sum__sum']:
            company_transactions_buyer_send = company_transactions_buyer_send['cash_sum__sum']
        else:
            company_transactions_buyer_send = 0

        company_transactions_seller_get = CashTransaction.objects.filter(
            slug=load, buyer_seller='seller', transaction_name=1, executed=True).aggregate(Sum('cash_sum'))
        company_transactions_seller_send = CashTransaction.objects.filter(
            slug=load, buyer_seller='seller', transaction_name=2, executed=True).aggregate(Sum('cash_sum'))
        if company_transactions_seller_get['cash_sum__sum']:
            company_transactions_seller_get = company_transactions_seller_get['cash_sum__sum']
        else:
            company_transactions_seller_get = 0
        if company_transactions_seller_send['cash_sum__sum']:
            company_transactions_seller_send = company_transactions_seller_send['cash_sum__sum']
        else:
            company_transactions_seller_send = 0

    else:
        if load.stat_id == 6:
            load_sell_price = 0
        elif load.stat_id == 7:
            load_sell_price = 0
        else:
            if BuyerLoad.objects.filter(slug=load_slug).exists():
                bayer = get_object_or_404(BuyerLoad, slug=load_slug)
                load_sell_price = bayer.load_sell_price
            else:
                load_sell_price = 0

        company_transactions_buyer_send = load_sell_price
        company_transactions_buyer_get = 0

        if load.stat_id == 6:
            load_buy_price = 0
        elif load.stat_id == 7:
            load_buy_price = 0
        else:
            seller_load_sum = SellerLoad.objects.filter(slug=load_slug)
            load_buy_price = 0
            for s in seller_load_sum:
                load_buy_price += s.load_buy_price

        company_transactions_seller_send = 0
        company_transactions_seller_get = load_buy_price

    buyer_get_send = company_transactions_buyer_send - company_transactions_buyer_get

    seller_get_send = company_transactions_seller_get - company_transactions_seller_send

    load_profit = seller_get_send - buyer_get_send

    context = {
        'buyer_get_send': buyer_get_send,
        'seller_get_send': seller_get_send,
        'load_profit': load_profit,
    }
    return context


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@transaction.atomic
def add_doc(request):
    if request.method == 'POST':
        load_ms = QuikAddLoadForm(request.POST)
        form_load = DocSellerForm(request.POST, request.FILES)
        if form_load.is_valid() and load_ms.is_valid():

            form_load_ = copy.copy(form_load.cleaned_data)
            load_ms_ = copy.copy(load_ms.cleaned_data)
            load_number = generation_number()

            if not Company.objects.filter(company_mc=load_ms_['seller_MC']).exists():
                info_seller_ms = get_mc_info(load_ms_['seller_MC'])
                new_company = Company.objects.create(company_mc=load_ms_['seller_MC'],
                                                     company_dot=info_seller_ms['dotNumber'],
                                                     company_name=info_seller_ms['legalName'],
                                                     company_address=f"{info_seller_ms['phyStreet']} "
                                                                     f"{info_seller_ms['phyCity']}, "
                                                                     f"{info_seller_ms['phyState']} "
                                                                     f"{info_seller_ms['phyZipcode']}",
                                                     company_type=CompanyTypeName.objects.get(name='broker'),

                                                     )
            else:
                new_company = Company.objects.get(company_mc=load_ms_['seller_MC'])

            seller_load_data = {
                'slug': load_number,
                'seller_load_number': 'no info',
                'load_buy_price': 1,
                'pickup_data': datetime.datetime(1000, 1, 1),
                'pickup_time_from': '00:00',
                'pickup_time_to': '00:00',
                'pickup_location': 'no info',
                'pickup_instructions': 'no info',
                'destination_data': datetime.datetime(1000, 1, 1),
                'destination_time_from': '00:00',
                'destination_time_to': '00:00',
                'destination_location': 'no info',
                'destination_instructions': 'no info',
                'company_mc': new_company,
                'seller_MC': load_ms_['seller_MC'],
            }
            seller_load = SellerLoad.objects.create(**seller_load_data)
            form_load_['slug'] = seller_load.pk
            DocSeller.objects.create(**form_load_)

            if UserCompany.objects.filter(user=request.user).exists() and request.user.usercompany.load_broker_default != None:
                company_broker = Company.objects.get(company_mc=request.user.usercompany.load_broker_default)
            else:
                company_broker = Company.objects.get(company_type=1, company_default='default')

            if UserCompany.objects.filter(user=request.user).exists() and request.user.usercompany.load_carrier_default != None:
                company_carrier = Company.objects.get(company_mc=request.user.usercompany.load_carrier_default)
            else:
                company_carrier = Company.objects.get(company_type=2, company_default='default')

            load_data = {
                'slug': load_number,
                'load_buy_price': 0.001,
                'load_sell_price': 0.001,
                'load_broker': company_broker,
                'load_prefix_broker': company_broker.company_prefix,
                'load_carrier': company_carrier,
                'user': request.user,
            }
            Load.objects.create(**load_data)

            return redirect('load', load_number)

        else:
            form_load.add_error(None, "Adding error")
    else:
        company_broker = Company.objects.filter(company_type=1, company_default='default').exists()
        company_carrier = Company.objects.filter(company_type=2, company_default='default').exists()
        form_load = DocSellerForm(initial={'doc': 4})
        load_ms = QuikAddLoadForm()
        context = {
            'load_broker': company_broker,
            'load_carrier': company_carrier,
            'load_ms': load_ms,
            'form_load': form_load,
            'title': 'Quik Add Load',
        }
        return render(request, 'transport/add_doc.html', context=context)


def mytask(request):
    context = {
        'title': 'My tasks',
    }

    return render(request, 'transport/mytask.html', context=context)


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def load_list(request):
    context = {
        'title': 'Load list',
    }

    return render(request, 'transport/load_list.html', context=context)


def finance(request):
    company_holding = Company.objects.filter(part_holding=True)
    user = request.user
    if user.groups.filter(name='Broker').exists():
        if user.usercompany.user_company is not None:
            to_pay_sum = CashTransaction.objects.filter(transaction_name=2,
                                                        broker_carrier_mc_id=user.usercompany.user_company.id,
                                                        executed=False).aggregate(cash_sum=Sum('cash_sum'))
            to_pay_sum = to_pay_sum['cash_sum']
        else:
            to_pay_sum = 0
    else:
        to_pay_sum = CashTransaction.objects.filter(transaction_name=2, executed=False).aggregate(cash_sum=Sum('cash_sum'))
        to_pay_sum = to_pay_sum['cash_sum']

    payment_expected_ = CashTransaction.objects.filter(transaction_name=1, executed=False).aggregate(
        cash_sum=Sum('cash_sum'))
    payment_expected_ = payment_expected_['cash_sum']
    company_invoice = CashTransactionCompanyInvoiceForm()
    context = {
        'company_invoice': company_invoice,
        'company_holding': company_holding,
        'payment_expected': payment_expected_,
        'to_pay_sum': to_pay_sum,
        'title': 'Finance',
        'title_create_invoice': '+ Create invoice',
        'button_create_invoice': 'Create'
    }

    return render(request, 'transport/finance.html', context=context)


def to_pay(request):
    user = request.user
    if user.groups.filter(name='Broker').exists():
        if UserCompany.objects.filter(user_id=user.id).exists() and user.usercompany.user_company is not None:
            to_pay_for_load = CashTransaction.objects.filter(transaction_name=2,
                                                             broker_carrier_mc_id=user.usercompany.user_company.id).\
                order_by('executed', 'transaction_data')
            to_pay_sum = CashTransaction.objects.filter(transaction_name=2,
                                                        broker_carrier_mc_id=user.usercompany.user_company.id,
                                                        executed=False).aggregate(cash_sum=Sum('cash_sum'))
            to_pay_sum = to_pay_sum['cash_sum']
        else:
            to_pay_for_load = None
            to_pay_sum = None

    else:
        to_pay_for_load = CashTransaction.objects.filter(transaction_name=2, ).order_by('executed', 'transaction_data')
        to_pay_sum = CashTransaction.objects.filter(transaction_name=2,
                                                    executed=False).aggregate(cash_sum=Sum('cash_sum'))
        to_pay_sum = to_pay_sum['cash_sum']

    to_pay_finance_form = CashTransactionFinanceForm()
    context = {
        'to_pay_for_load': to_pay_for_load,
        'to_pay_finance_form': to_pay_finance_form,
        'to_pay_sum': to_pay_sum,
        'title': 'To pay',
        'title_finance_to_pay_button': 'Apply',
    }

    return render(request, 'transport/to_pay.html', context=context)


def payment_expected(request):
    payment_expected_for_load = CashTransaction.objects.filter(transaction_name=1, ) \
        .order_by('executed', 'transaction_data')
    payment_expected_sum = CashTransaction.objects.filter(transaction_name=1, executed=False) \
        .aggregate(cash_sum=Sum('cash_sum'))
    payment_expected_sum = payment_expected_sum['cash_sum']

    payment_expected_finance_form = CashTransactionFinanceForm()
    context = {
        'payment_expected_for_load': payment_expected_for_load,
        'payment_expected_finance_form': payment_expected_finance_form,
        'payment_expected_sum': payment_expected_sum,
        'title': 'Payment expected',
        'title_finance_payment_expected_button': 'Apply',
    }

    return render(request, 'transport/payment_expected.html', context=context)


def company_transaction(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)
    # print(company)
    transaction_comp = CashTransaction.objects.filter(executed=True).exclude(slug=None)
    # print(transaction_comp)

    transaction_dict_broker = dict()
    transaction_dict_carrier = dict()

    name_c = ''
    sum_c = 0
    sum_send = 0.00
    for cash in transaction_comp:
        # print(cash.slug, cash.buyer_seller, cash.transaction_name, cash.slug.load_carrier)
        if cash.slug.load_carrier == company and str(cash.buyer_seller) == 'buyer' \
                and str(cash.transaction_name) == 'sent payment':
            current_name_c = cash.slug.load_broker.company_name
            if current_name_c != name_c:
                sum_c = 0
                sum_c += cash.cash_sum
                name_c = cash.slug.load_broker.company_name
                if sum_send == 0.00:
                    sum_send = CashTransaction.objects.filter(slug=None,
                                                              broker_carrier_mc=company,
                                                              buyer_seller_mc=cash.slug.load_broker,
                                                              transaction_name=2,
                                                              executed=True).aggregate(Sum('cash_sum'))
                    if sum_send['cash_sum__sum'] is not None:
                        sum_c = sum_c - sum_send['cash_sum__sum']
                transaction_dict_broker.update([(name_c, sum_c)])
            else:
                sum_c += cash.cash_sum
                name_c = cash.slug.load_broker.company_name
                transaction_dict_broker.update([(name_c, sum_c)])

        if cash.slug.load_broker == company and str(cash.buyer_seller) == 'buyer' \
                and str(cash.transaction_name) == 'sent payment':
            # print(cash.slug, cash.slug.load_carrier.company_name, cash.transaction_name, cash.cash_sum)
            current_name_c = cash.slug.load_carrier.company_name
            if current_name_c != name_c:
                sum_c = 0
                sum_c += cash.cash_sum
                name_c = cash.slug.load_carrier.company_name
                if sum_send == 0.00:
                    sum_send = CashTransaction.objects.filter(slug=None,
                                                              broker_carrier_mc=company,
                                                              buyer_seller_mc=cash.slug.load_carrier,
                                                              transaction_name=1,
                                                              executed=True).aggregate(Sum('cash_sum'))
                    if sum_send['cash_sum__sum'] is not None:
                        sum_c = sum_c - sum_send['cash_sum__sum']
                transaction_dict_carrier.update([(name_c, sum_c)])
            else:
                sum_c += cash.cash_sum
                name_c = cash.slug.load_carrier.company_name
                transaction_dict_carrier.update([(name_c, sum_c)])

    # print(transaction_dict_broker)
    # print(transaction_dict_carrier)

    transaction_company = CashTransaction.objects.filter(broker_carrier_mc=company_pk,

                                                         ).order_by('executed', 'transaction_data')

    receive_sum = CashTransaction.objects.filter(broker_carrier_mc=company_pk,
                                                 transaction_name=1, executed=True).aggregate(cash_sum=Sum('cash_sum'))
    receive_sum = receive_sum['cash_sum']

    payment_expected_ = CashTransaction.objects.filter(broker_carrier_mc=company_pk,
                                                       transaction_name=1,
                                                       executed=False).aggregate(cash_sum=Sum('cash_sum'))
    payment_expected_ = payment_expected_['cash_sum']

    sent_sum = CashTransaction.objects.filter(broker_carrier_mc=company_pk,
                                              transaction_name=2,
                                              executed=True).aggregate(cash_sum=Sum('cash_sum'))
    sent_sum = sent_sum['cash_sum']

    to_pay_ = CashTransaction.objects.filter(broker_carrier_mc=company_pk,
                                             transaction_name=2,
                                             executed=False).aggregate(cash_sum=Sum('cash_sum'))
    to_pay_ = to_pay_['cash_sum']

    if type(payment_expected_) != decimal.Decimal:
        payment_expected_ = 0

    if type(to_pay_) != decimal.Decimal:
        to_pay_ = 0

    payment_form = CashTransactionCompanyForm()
    data_rang_form = DataRangCompanyTransaction()

    if type(receive_sum) != decimal.Decimal:
        receive_sum = 0

    if type(sent_sum) != decimal.Decimal:
        sent_sum = 0

    balance = receive_sum - sent_sum

    context = {
        'transaction_dict_carrier': transaction_dict_carrier,
        'transaction_dict_broker': transaction_dict_broker,
        'to_pay': to_pay_,
        'payment_expected': payment_expected_,
        'balance': balance,
        'title_payment': '+ Add transaction',
        'title_transaction': 'Add transaction',
        'title_create': 'Show pdf list transaction',
        'title_show': 'Show pdf',
        'payment_form': payment_form,
        'data_rang_form': data_rang_form,
        'receive_sum': receive_sum,
        'sent_sum': sent_sum,
        'title': company.company_name,
        'company_pk': company_pk,
        'transaction_company': transaction_company,
    }

    return render(request, 'transport/company_transaction.html', context=context)


@transaction.atomic
def add_transaction_company_save(request, company_pk):
    if request.method == 'POST':
        form_load = request.POST.copy()

        form_load['buyer_seller_mc'] = get_object_or_404(Company, pk=form_load['buyer_seller_mc'])
        form_load['broker_carrier_mc'] = get_object_or_404(Company, pk=company_pk)
        form_load['buyer_seller'] = 'company'
        form_load['counterparty'] = 'company'
        form = CashTransactionCompanyForm(form_load, request.FILES)

        if form.is_valid():
            try:
                obj = form.save()

                return redirect('show_info_pay', obj.id)

            except:
                form.add_error(None, "Adding error")

        return redirect('company_transaction', company_pk)


@transaction.atomic
def show_info_pay(request, to_pay_id):
    show_to_pay_load = get_object_or_404(CashTransaction, pk=to_pay_id)
    company = get_object_or_404(Company, company_mc=show_to_pay_load.broker_carrier_mc)

    form_to_pay = CashTransactionFinanceForm(initial={'cash_sum': show_to_pay_load.cash_sum,
                                                      'transaction_data': show_to_pay_load.transaction_data,
                                                      'comment': show_to_pay_load.comment,
                                                      'executed': show_to_pay_load.executed,
                                                      'buyer_seller_mc': show_to_pay_load.buyer_seller_mc,
                                                      })
    if show_to_pay_load.slug is not None:
        load = get_object_or_404(Load, slug=show_to_pay_load.slug)
    else:
        load = None

    if show_to_pay_load.transaction_name_id == 1:
        title = 'Payment expected'
        title_edit = 'Payment expected info save'
    elif show_to_pay_load.transaction_name_id == 2:
        title = 'To pay'
        title_edit = 'Pay info save'

    if show_to_pay_load.executed and show_to_pay_load.transaction_name_id == 1:
        title = 'Payment received'
    elif show_to_pay_load.executed and show_to_pay_load.transaction_name_id == 2:
        title = 'Paid'

    context = {
        'load': load,
        'show_to_pay': show_to_pay_load,
        'title': title,
        'title_edit': title_edit,
        'to_pay_id': to_pay_id,
        'form_to_pay': form_to_pay,
        'company_pk': company.pk,
    }

    return render(request, 'transport/show_info_pay.html', context=context)


@transaction.atomic
def to_pay_save(request, to_pay_id):
    if request.method == 'POST':
        form_to_pay = CashTransactionFinanceForm(request.POST)
        if form_to_pay.is_valid():
            try:
                cash_transaction = CashTransaction.objects.get(pk=to_pay_id)

                data = copy.copy(form_to_pay.cleaned_data)

                CashTransaction.objects.filter(pk=to_pay_id).update(cash_sum=data['cash_sum'],
                                                                    transaction_data=data['transaction_data'],
                                                                    comment=data['comment'],
                                                                    executed=data['executed'],
                                                                    )
                if cash_transaction.slug is not None:
                    get_sent_profit_data = get_sent_profit(cash_transaction.slug.slug)
                    Load.objects.filter(slug=cash_transaction.slug.slug). \
                        update(load_buy_price=get_sent_profit_data['seller_get_send'],
                               load_sell_price=get_sent_profit_data['buyer_get_send'],
                               load_profit=get_sent_profit_data['load_profit'])

                return redirect('show_info_pay', to_pay_id)
            except:
                form_to_pay.add_error(None, 'Add error')
    else:
        form_to_pay = CashTransactionFinanceForm()
    context = {
        'title': 'To pay',
        'form_to_pay': form_to_pay,
    }
    return render(request, 'transport/to_pay.html', context=context)


@transaction.atomic
def setting(request):
    broker = Company.objects.filter(company_type=1, part_holding=True)
    carrier = Company.objects.filter(company_type=2, part_holding=True)
    holding_company_form = CompanyForm()

    if Company.objects.filter(company_type=1, company_default='default').count() == 1:
        data_broker = Company.objects.get(company_type=1, part_holding=True, company_default='default')
        broker_default = data_broker.id
    else:
        broker_default = None

    if Company.objects.filter(company_type=2, company_default='default').count() == 1:
        data_carrier = Company.objects.get(company_type=2, part_holding=True, company_default='default')
        carrier_default = data_carrier.id
    else:
        carrier_default = None

    initial = {'company_broker_default': broker_default, 'company_carrier_default': carrier_default}

    default_set_form = SetDefaultCompanySettingForm(initial=initial)

    context = {
        'title': 'Setting',
        'button_user_list': 'Show User list',
        'title_broker_carrier': 'Broker and Carrier',
        'title_add_broker': '+ Add company',
        'title_add': 'Add company',
        'holding_company_form': holding_company_form,
        'broker': broker,
        'carrier': carrier,
        'default_set_form': default_set_form,
        'title_default_set': 'Default set Carrier and Broker',
        'set_default': 'Set Default',
        'title_company_broker': 'Edit company',
        'save': 'Save',
        'button_company_list': 'Show Company list'
    }
    return render(request, 'transport/setting.html', context=context)


@transaction.atomic
def add_holding_company(request):
    successfully = ''
    if request.method == 'POST':
        broker_form = CompanyForm(request.POST, request.FILES)
        if broker_form.is_valid():
            data_form = copy.copy(broker_form.cleaned_data)
            info_broker_ms = get_mc_info(data_form['company_mc'])
            info_broker = {
                'company_dot': info_broker_ms['dotNumber'],
                'company_name': info_broker_ms['legalName'],
                'company_address': f"{info_broker_ms['phyStreet']} {info_broker_ms['phyCity']}, "
                                   f"{info_broker_ms['phyState']} {info_broker_ms['phyZipcode']}",
                'part_holding': True,
            }
            data_form.update(info_broker)
            Company.objects.create(**data_form)

            if Company.objects.filter(company_type=1).count() == 1:
                Company.objects.filter(company_type=1).update(company_default='default')

            if Company.objects.filter(company_type=2).count() == 1:
                Company.objects.filter(company_type=2).update(company_default='default')

            successfully = 'Company added successfully'
            broker_form = CompanyForm()
            #return redirect('setting')

        else:
            broker_form.add_error(None, "Adding error")

    else:
        broker_form = CompanyForm()

    context = {
        'successfully': successfully,
        'title': 'Add Holding Company',
        'title_add': 'Add Company',
        'broker_form': broker_form,
    }
    return render(request, 'transport/add_holding_company.html', context=context)


def company_list(request):
    company_list_data = Company.objects.all().order_by('-part_holding', 'company_mc')

    context = {
        'title': 'Company list',
        'company_list_data': company_list_data,
    }

    return render(request, 'transport/company_list.html', context=context)


def show_user_list(request):
    user_lt = User.objects.filter(is_staff=False).order_by('-is_active')
    context = {
        'title': 'User list',
        'user_lt': user_lt,
        'title_add_user': '+ Add user',
        'button_add': 'Add new user'
    }

    return render(request, 'transport/user_list.html', context=context)


@transaction.atomic
def add_user(request):
    if request.method == 'POST':
        user_form = RegisterUserForm(request.POST)
        if user_form.is_valid():
            data_form = copy.copy(user_form.cleaned_data)
            user = user_form.save()
            user.groups.set(data_form['groups'])
            UserCompany.objects.create(user=user)
            # for i in data_form['groups']:
            # my_group = Group.objects.get(name=i)
            # my_group.user_set.add(user)

            return redirect('show_user_list')
    else:
        user_form = RegisterUserForm()

    context = {
        'title': 'Add User',
        'user_form': user_form,
        'button_add': 'Add new user'
    }

    return render(request, 'transport/add_user.html', context=context)


@transaction.atomic
def show_user(request, username):
    user = get_object_or_404(User, username=username)
    successfully = ''
    if request.method == 'POST':
        user_form = request.POST.copy()
        User.objects.filter(username=username).update(last_name=user_form['last_name'],
                                                      first_name=user_form['first_name'],
                                                      email=user_form['email'],
                                                      )

        if user_form['user_company']:
            company = get_object_or_404(Company, id=user_form['user_company'])
            UserCompany.objects.filter(user=user).update(user_company=company)
        else:
            UserCompany.objects.filter(user=user).update(user_company='')

        if user_form['load_broker_default']:
            company = get_object_or_404(Company, id=user_form['load_broker_default'])
            UserCompany.objects.filter(user=user).update(load_broker_default=company)
        else:
            UserCompany.objects.filter(user=user).update(load_broker_default='')

        if user_form['load_carrier_default']:
            company = get_object_or_404(Company, id=user_form['load_carrier_default'])
            UserCompany.objects.filter(user=user).update(load_carrier_default=company)
        else:
            UserCompany.objects.filter(user=user).update(load_carrier_default='')

        try:
            if user_form['is_active']:
                User.objects.filter(username=username).update(is_active=True)
        except:
            User.objects.filter(username=username).update(is_active=False)

        user.groups.set(user_form.getlist('groups'))

        successfully = 'User change successfully'
        user = get_object_or_404(User, username=username)

    data = {'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'groups': user.groups.all,
            'is_active': user.is_active,
            'user_company': user.usercompany.user_company,
            'load_broker_default': user.usercompany.load_broker_default,
            'load_carrier_default': user.usercompany.load_carrier_default,
            }
    change_user_form = ChangeUserForm(initial=data)

    context = {
        'successfully': successfully,
        'username': username,
        'title': f"Edit User / {username} /",
        'user_form_change': change_user_form,
        'button_add': 'Edit user',
        'title_pass': f"Change password / {username} /",
    }

    return render(request, 'transport/show_user.html', context=context)


@transaction.atomic
def change_user_password(request, username):
    add_error = ''
    if request.method == 'POST':
        user_form = request.POST.copy()
        if user_form['new_password1'] != '' and user_form['new_password2'] != '':
            if user_form['new_password1'] == user_form['new_password2']:
                u = get_object_or_404(User, username=username)
                new_password = user_form['new_password1']
                u.set_password(new_password)
                u.save()
                return redirect('show_user', username)
            else:
                add_error = "The password doesn't match"

    edit_user_form = EditUserForm(username)

    context = {
        'add_error': add_error,
        'title': f"Edit User / {username} /",
        'user_form': edit_user_form,
        'button_add': 'Edit user',
        'title_pass': f"Change password / {username} /",
        'button_change_pass': 'Change password'
    }

    return render(request, 'transport/change_user_password.html', context=context)


def show_company(request, pk):
    company_data = get_object_or_404(Company, pk=pk)
    company_form = CompanyFullForm(instance=company_data)

    context = {
        'title': 'Company info',
        'pk': pk,
        'company_form': company_form,
        'save': 'Save',
    }
    return render(request, 'transport/show_company.html', context=context)


@transaction.atomic
def company_save(request, pk):
    if request.method == 'POST':
        company_form_ = request.POST.copy()
        files_form = request.FILES.copy()
        inst = get_object_or_404(Company, pk=pk)
        check_file = inst.company_logo
        if check_file:
            storage, path = inst.company_logo.storage, inst.company_logo.path

        if str(inst) != str(company_form_['company_mc']):
            info_seller_ms = get_mc_info(company_form_['company_mc'])
            company_form_.update(company_dot=info_seller_ms['dotNumber'],
                                 company_name=info_seller_ms['legalName'],
                                 company_address=f"{info_seller_ms['phyStreet']} "
                                                 f"{info_seller_ms['phyCity']}, "
                                                 f"{info_seller_ms['phyState']} "
                                                 f"{info_seller_ms['phyZipcode']}",
                                 )

        company_form = CompanyFullForm(company_form_ or None, files_form or None, instance=inst)
        successfully = ''
        if company_form.is_valid():
            company_form.save()

            if files_form:
                if check_file:
                    storage.delete(path)

            successfully = 'Company change successfully'
            instance = get_object_or_404(Company, pk=pk)
            company_form = CompanyFullForm(instance=instance)

        else:
            company_form.add_error(None, "Adding error")

    else:
        company_form = CompanyFullForm()

    context = {
        'pk': pk,
        'successfully': successfully,
        'title': 'Company info',
        'company_form': company_form,
        'save': 'Save',
    }
    return render(request, 'transport/show_company.html', context=context)


@transaction.atomic
def delete_company_payment(request, doc_id):
    company_payment = get_object_or_404(CashTransaction, id=doc_id)

    if request.method == 'POST':
        try:
            company_payment.delete()

            return redirect('company_transaction', company_payment.broker_carrier_mc.pk)
        except:
            return redirect('company_transaction', company_payment.broker_carrier_mc.pk)


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'transport/login_u.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Authentication'
        context['button_login'] = 'login'
        return context

    def get_success_url(self):
        return reverse('home')


def logout_user(request):
    logout(request)
    return redirect('login_u')


def pageNotFound(request, exception):
    return HttpResponseNotFound('<h1>Page not found</h1>')


def show_load(request, load_slug):
    load = get_object_or_404(Load, slug=load_slug)
    load_form = AddLoadForm(instance=load)
    load_slug = load_slug
    context = {
        'load_slug': load_slug,
        'load_form': load_form,
        'load': load,
        'title': load.slug,
    }
    return render(request, 'transport/load.html', context=context)


def show_seller_load(request, seller_id):
    load = get_object_or_404(SellerLoad, pk=seller_id)
    load_form = AddLoadForm(instance=load)
    seller_id = seller_id
    context = {
        'seller_id': seller_id,
        'load_form': load_form,
        'load': load,
        'title': load.slug,
    }
    return render(request, 'transport/load.html', context=context)


@transaction.atomic
def buyer_load_info(request):
    if request.method == 'POST':
        form_load = request.POST.copy()
        load_number = form_load['slug']

        if not Company.objects.filter(company_mc=form_load['buyer_MC']).exists():
            info_buyer_ms = get_mc_info(form_load['buyer_MC'])
            new_company = Company.objects.create(company_mc=form_load['buyer_MC'],
                                                 company_dot=info_buyer_ms['dotNumber'],
                                                 company_name=info_buyer_ms['legalName'],
                                                 company_address=f"{info_buyer_ms['phyStreet']} "
                                                                 f"{info_buyer_ms['phyCity']}, "
                                                                 f"{info_buyer_ms['phyState']} "
                                                                 f"{info_buyer_ms['phyZipcode']}",
                                                 company_type=CompanyTypeName.objects.get(name='carrier'),
                                                 )
        else:
            new_company = Company.objects.get(company_mc=form_load['buyer_MC'])

        info_buyer = {
            'company_mc': new_company,
        }

        form_load.update(info_buyer)
        form = BuyerForm(form_load or None)
        if form.is_valid():
            try:
                form.save()
                load_stat = Load.objects.get(slug=load_number)
                if load_stat.stat_id != 5:
                    Load.objects.filter(slug=load_number).update(stat=4, load_sell_price=form_load['load_sell_price'])

                return redirect('load', load_number)

            except:
                form_load.add_error(None, "Adding error")

        return redirect('load', load_number)


@transaction.atomic
def buyer_load_edit(request):
    if request.method == 'POST':
        form_load = request.POST.copy()
        load_number = form_load['slug']
        instance = get_object_or_404(BuyerLoad, slug=load_number)

        if str(instance.buyer_MC) != str(form_load['buyer_MC']):

            if not Company.objects.filter(company_mc=form_load['buyer_MC']).exists():

                info_buyer_ms = get_mc_info(form_load['buyer_MC'])
                new_company = Company.objects.create(company_mc=form_load['buyer_MC'],
                                                     company_dot=info_buyer_ms['dotNumber'],
                                                     company_name=info_buyer_ms['legalName'],
                                                     company_address=f"{info_buyer_ms['phyStreet']} "
                                                                     f"{info_buyer_ms['phyCity']}, "
                                                                     f"{info_buyer_ms['phyState']} "
                                                                     f"{info_buyer_ms['phyZipcode']}",
                                                     company_type=CompanyTypeName.objects.get(name='carrier'),
                                                     )
            else:
                new_company = Company.objects.get(company_mc=form_load['buyer_MC'])
        else:
            new_company = Company.objects.get(company_mc=form_load['buyer_MC'])
        info_buyer = {
            'company_mc': new_company,
        }
        form_load.update(info_buyer)

        form = BuyerForm(form_load or None, instance=instance)
        if form.is_valid():
            try:
                form.save()

                context = get_sent_profit(load_number)
                Load.objects.filter(slug=load_number).update(load_sell_price=context['buyer_get_send'])

                return redirect('load', load_number)
            except:
                form_load.add_error(None, "Adding error")

        return redirect('load', load_number)


@transaction.atomic
def seller_documents(request):
    if request.method == 'POST':
        form_load = AddDocSellerForm(request.POST, request.FILES)
        if form_load.is_valid():
            try:
                form_load = copy.copy(form_load.cleaned_data)
                load_number = get_object_or_404(SellerLoad, pk=form_load['slug'])
                DocSeller.objects.create(**form_load)

                return redirect('load', load_number.slug)

            except:
                form_load.add_error(None, "Adding error")
    else:
        form_load = AddDocSellerForm()
        context = {
            'form_load': form_load,
        }
        return render(request, 'transport/load.html', context=context)


@transaction.atomic
def delete_seller_doc(request, doc_id):
    seller_doc = get_object_or_404(DocSeller, id=doc_id)
    seller_load = get_object_or_404(SellerLoad, pk=seller_doc.slug)
    if request.method == 'POST':
        try:
            seller_doc.delete()
            return redirect('load', seller_load.slug)
        except:
            return redirect('load', seller_load.slug)


@transaction.atomic
def buyer_documents(request):
    if request.method == 'POST':
        form_load = AddDocBuyerForm(request.POST, request.FILES)
        if form_load.is_valid():
            try:
                form_load = copy.copy(form_load.cleaned_data)
                load_number = form_load['slug']
                DocBuyer.objects.create(**form_load)

                return redirect('load', load_number)

            except:
                form_load.add_error(None, "Adding error")
    else:
        form_load = AddDocBuyerForm()
        context = {
            'form_load': form_load,
        }
        return render(request, 'transport/load.html', context=context)


@transaction.atomic
def delete_buyer_doc(request, doc_id):
    buyer_doc = get_object_or_404(DocBuyer, id=doc_id)
    if request.method == 'POST':
        try:
            buyer_doc.delete()
            return redirect('load', buyer_doc)
        except:
            return redirect('load', buyer_doc)


@transaction.atomic
def seller_load_save(request, s_load_id):
    if request.method == 'POST':
        form_load = request.POST.copy()
        load_number = form_load['slug']
        instance = SellerLoad.objects.get(pk=s_load_id)

        if str(instance.seller_MC) != str(form_load['seller_MC']):

            if not Company.objects.filter(company_mc=form_load['seller_MC']).exists():

                info_seller_ms = get_mc_info(form_load['seller_MC'])
                new_company = Company.objects.create(company_mc=form_load['seller_MC'],
                                                     company_dot=info_seller_ms['dotNumber'],
                                                     company_name=info_seller_ms['legalName'],
                                                     company_address=f"{info_seller_ms['phyStreet']} "
                                                                     f"{info_seller_ms['phyCity']}, "
                                                                     f"{info_seller_ms['phyState']} "
                                                                     f"{info_seller_ms['phyZipcode']}",
                                                     company_type=CompanyTypeName.objects.get(name='broker'),
                                                     )
            else:
                new_company = Company.objects.get(company_mc=form_load['seller_MC'])
        else:
            new_company = Company.objects.get(company_mc=form_load['seller_MC'])

        info_seller = {
            'company_mc': new_company,
        }
        form_load.update(info_seller)

        form = AddSellerLoadForm(form_load or None, instance=instance)
        if form.is_valid():
            try:
                form.save()

                load_stat = get_object_or_404(Load, slug=load_number)

                if str(load_stat.stat) == 'created':
                    Load.objects.filter(slug=load_number).update(stat=3)

                context = get_sent_profit(load_number)
                Load.objects.filter(slug=load_number).update(load_buy_price=context['seller_get_send'])

                return redirect('load', load_number)

            except:
                form_load.add_error(None, "Adding error")

        return redirect('load', load_number)


@transaction.atomic
def seller_load_add(request):
    if request.method == 'POST':
        form_load = request.POST.copy()
        load_number = form_load['slug']

        if not Company.objects.filter(company_mc=form_load['seller_MC']).exists():

            info_seller_ms = get_mc_info(form_load['seller_MC'])
            new_company = Company.objects.create(company_mc=form_load['seller_MC'],
                                                 company_dot=info_seller_ms['dotNumber'],
                                                 company_name=info_seller_ms['legalName'],
                                                 company_address=f"{info_seller_ms['phyStreet']} "
                                                                 f"{info_seller_ms['phyCity']}, "
                                                                 f"{info_seller_ms['phyState']} "
                                                                 f"{info_seller_ms['phyZipcode']}",
                                                 company_type=CompanyTypeName.objects.get(name='broker'),
                                                 )
        else:
            new_company = Company.objects.get(company_mc=form_load['seller_MC'])

        info_seller = {
            'company_mc': new_company,
        }
        form_load.update(info_seller)

        form = AddSellerLoadForm(form_load or None)
        if form.is_valid():
            try:
                form.save()

                seller_load_sum = SellerLoad.objects.filter(slug=load_number)
                load_buy_price = 0
                for s in seller_load_sum:
                    load_buy_price += s.load_buy_price
                Load.objects.filter(slug=load_number).update(load_buy_price=load_buy_price)

                return redirect('load', load_number)

            except:
                form_load.add_error(None, "Adding error")

        return redirect('load', load_number)


@transaction.atomic
def cash_transaction_seller_add(request, pk_load):
    if request.method == 'POST':
        seller_load = SellerLoad.objects.get(pk=pk_load)
        load = get_object_or_404(Load, slug=seller_load.slug)
        form_load = request.POST.copy()
        form_load['slug'] = load
        form_load['broker_carrier_mc'] = get_object_or_404(Company, company_mc=load.load_carrier)
        form_load['buyer_seller_mc'] = get_object_or_404(Company, company_mc=seller_load.seller_MC)
        form_load['buyer_seller'] = 'seller'
        form_load['counterparty'] = pk_load
        load_number = seller_load.slug
        form = CashTransactionForm(form_load, request.FILES)
        if form.is_valid():
            try:
                form.save()
                stat_load = status_load(load)
                Load.objects.filter(slug=load_number).update(stat=stat_load)
                context = get_sent_profit(load_number)
                Load.objects.filter(slug=load_number).update(load_buy_price=context['seller_get_send'],
                                                             load_sell_price=context['buyer_get_send'])

                return redirect('load', load_number)

            except:
                form_load.add_error(None, "Adding error")

        return redirect('load', load_number)


@transaction.atomic
def cash_transaction_buyer_add(request, buyer_pk):
    if request.method == 'POST':
        buyer_load = BuyerLoad.objects.get(pk=buyer_pk)
        load = get_object_or_404(Load, slug=buyer_load.slug)
        form_load = request.POST.copy()
        form_load['slug'] = load
        form_load['broker_carrier_mc'] = get_object_or_404(Company, company_mc=load.load_broker)
        form_load['buyer_seller_mc'] = get_object_or_404(Company, company_mc=buyer_load.buyer_MC)
        form_load['buyer_seller'] = 'buyer'
        form_load['counterparty'] = buyer_pk
        load_number = buyer_load.slug
        form = CashTransactionForm(form_load, request.FILES)
        if form.is_valid():
            try:
                form.save()
                stat_load = status_load(load)
                Load.objects.filter(slug=load_number).update(stat=stat_load)
                context = get_sent_profit(load_number)
                Load.objects.filter(slug=load_number).update(load_buy_price=context['seller_get_send'],
                                                             load_sell_price=context['buyer_get_send'])

                return redirect('load', load_number)

            except:
                form_load.add_error(None, "Adding error")

        return redirect('load', load_number)


@transaction.atomic
def delete_seller_payment(request, doc_id):
    seller_doc = get_object_or_404(CashTransaction, id=doc_id)
    cash_transaction = CashTransaction.objects.filter(slug=seller_doc.slug).count()
    if request.method == 'POST':
        try:
            seller_doc.delete()
            if cash_transaction == 1:
                buyer_load_sum = BuyerLoad.objects.filter(slug=seller_doc.slug)
                seller_load_sum = SellerLoad.objects.filter(slug=seller_doc.slug)

                load_sell_price = 0
                for s in buyer_load_sum:
                    load_sell_price += s.load_sell_price

                load_buy_price = 0
                for s in seller_load_sum:
                    load_buy_price += s.load_buy_price

                load = seller_doc.slug
                stat_load = status_load(load)
                Load.objects.filter(slug=seller_doc.slug).update(stat=stat_load,
                                                                 load_buy_price=load_buy_price,
                                                                 load_sell_price=load_sell_price,
                                                                 load_profit=0.00)

            return redirect('load', seller_doc.slug)
        except:
            return redirect('load', seller_doc.slug)


def default_set_company(request):
    if request.method == 'POST':
        default_set_form = SetDefaultCompanySettingForm(request.POST)
        if default_set_form.is_valid():

            default_set_form = copy.copy(default_set_form.cleaned_data)
            Company.objects.filter(company_type=1, part_holding=True).update(company_default='')
            Company.objects.filter(company_type=2, part_holding=True).update(company_default='')
            Company.objects.filter(company_type=2,
                                   part_holding=True,
                                   company_mc=default_set_form['company_carrier_default']) \
                .update(company_default='default')
            Company.objects.filter(company_type=1,
                                   part_holding=True,
                                   company_mc=default_set_form['company_broker_default']) \
                .update(company_default='default')

            return redirect('setting')

        else:
            default_set_form.add_error(None, "Adding error")

    else:
        default_set_form = SetDefaultCompanySettingForm()

    context = {
        'default_set_form': default_set_form,
    }
    return render(request, 'transport/setting.html', context=context)


@transaction.atomic
def set_user(request, load_slug):
    if request.method == 'POST':
        user_choice = UserChoiceForm(request.POST)
        if user_choice.is_valid():
            user_choice = copy.copy(user_choice.cleaned_data)
            if user_choice['user_name']:
                Load.objects.filter(slug=load_slug).update(user=user_choice['user_name'])
        else:
            user_choice.add_error(None, "Modify error")

    return redirect('load', load_slug)


@transaction.atomic
def set_status(request, load_slug):
    if request.method == 'POST':
        status_choice = SetStatus(request.POST)
        if status_choice.is_valid():
            status_choice = copy.copy(status_choice.cleaned_data)
            if status_choice['status_load'] == "1":
                Load.objects.filter(slug=load_slug).update(stat=7)
                get_sent_profit_data = get_sent_profit(load_slug)
                Load.objects.filter(slug=load_slug).update(load_buy_price=get_sent_profit_data['seller_get_send'],
                                                           load_sell_price=get_sent_profit_data['buyer_get_send'],
                                                           load_profit=get_sent_profit_data['load_profit'])
            elif status_choice['status_load'] == "2":
                Load.objects.filter(slug=load_slug).update(stat=6)
                get_sent_profit_data = get_sent_profit(load_slug)
                Load.objects.filter(slug=load_slug).update(load_buy_price=get_sent_profit_data['seller_get_send'],
                                                           load_sell_price=get_sent_profit_data['buyer_get_send'],
                                                           load_profit=get_sent_profit_data['load_profit'])
            elif status_choice['status_load'] == "3":
                Load.objects.filter(slug=load_slug).update(stat=1)
            elif status_choice['status_load'] == "4":
                stat_load = status_load(load_slug)
                if stat_load == 5:
                    Load.objects.filter(slug=load_slug).update(stat=5)
                    get_sent_profit_data = get_sent_profit(load_slug)
                    Load.objects.filter(slug=load_slug).update(load_buy_price=get_sent_profit_data['seller_get_send'],
                                                               load_sell_price=get_sent_profit_data['buyer_get_send'],
                                                               load_profit=get_sent_profit_data['load_profit'])
                elif stat_load == 4:
                    Load.objects.filter(slug=load_slug).update(stat=4)
                    get_sent_profit_data = get_sent_profit(load_slug)
                    Load.objects.filter(slug=load_slug).update(load_buy_price=get_sent_profit_data['seller_get_send'],
                                                               load_sell_price=get_sent_profit_data['buyer_get_send'],
                                                               load_profit=get_sent_profit_data['load_profit'])
                else:
                    Load.objects.filter(slug=load_slug).update(stat=3)
                    get_sent_profit_data = get_sent_profit(load_slug)
                    Load.objects.filter(slug=load_slug).update(load_buy_price=get_sent_profit_data['seller_get_send'],
                                                               load_sell_price=get_sent_profit_data['buyer_get_send'],
                                                               load_profit=get_sent_profit_data['load_profit'])

            return redirect('load', load_slug)

        else:
            status_choice.add_error(None, "Modify error")

    return redirect('load', load_slug)


@transaction.atomic
def set_company_load(request, load_slug):
    if request.method == 'POST':
        default_set_form = SetDefaultCompanyForm(request.POST)
        if default_set_form.is_valid():

            default_set_form = copy.copy(default_set_form.cleaned_data)
            load_mc = Load.objects.get(slug=load_slug)
            company_broker_prefix = Company.objects.get(company_mc=default_set_form['company_broker_default'])
            company_carrier_prefix = Company.objects.get(company_mc=default_set_form['company_carrier_default'])
            if str(load_mc.load_broker) != str(default_set_form['company_broker_default']):
                Load.objects.filter(slug=load_slug).update(load_broker=company_broker_prefix,
                                                           load_prefix_broker=company_broker_prefix.company_prefix)

            if str(load_mc.load_carrier) != str(default_set_form['company_carrier_default']):
                Load.objects.filter(slug=load_slug).update(
                    load_carrier=company_carrier_prefix,
                    load_prefix_broker=company_carrier_prefix.company_prefix)

            return redirect('load', load_slug)

        else:
            default_set_form.add_error(None, "Adding error")

    else:
        default_set_form = SetDefaultCompanyForm()

    context = {
        'default_set_form': default_set_form,
    }
    return render(request, 'transport/setting.html', context=context)
