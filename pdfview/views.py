import csv
from datetime import datetime

from django.db.models import Sum, Q
from django.shortcuts import render, get_object_or_404

from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

from transport.models import *
import transport.models


def export_load_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="load.csv"'
    writer = csv.writer(response)
    writer.writerow(['User',
                     'Date create',
                     'Load number',
                     'Status',
                     'Load buy price',
                     'Load sell price',
                     'Load profit'
                     ])

    data = Load.objects.filter(Q(stat=6) | Q(stat=7))
    loads = []
    for l in data:
        loads += [(l.user.username,
                   l.date_create,
                   l.load_prefix_broker + l.slug,
                   l.stat.name,
                   l.load_buy_price,
                   l.load_sell_price,
                   l.load_profit)]

    for load in loads:
        writer.writerow(load)
    return response


def render_pdf_view(request, *args, **kwargs):
    slug = kwargs.get('slug')
    load = get_object_or_404(transport.models.Load, slug=slug)
    seller = SellerLoad.objects.filter(slug=slug)
    buyer = get_object_or_404(transport.models.BuyerLoad, slug=slug)

    default_broker = Company.objects.filter(company_mc=load.load_broker)
    pk = None
    for i in default_broker:
        pk = i.pk

    company = get_object_or_404(Company, pk=pk)

    title = f'RC load #{load.load_prefix_broker}{slug}'
    title_rc = f'Rate Confirmation order number {load.load_prefix_broker}{slug}'

    template_path = 'pdfview/rate_con_pdf.html'
    context = {'load': load,
               'seller': seller,
               'buyer': buyer,
               'company': company,
               'title': title,
               'title_rc': title_rc,
               'load_number': f'{load.load_prefix_broker}{slug}',
               }
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="rate_con_{load.load_prefix_broker}{slug}.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def render_pdf_invoice_for_seller(request, *args, **kwargs):
    pk = kwargs.get('seller_pk')
    load = get_object_or_404(transport.models.SellerLoad, pk=pk)
    load_carr = get_object_or_404(transport.models.Load, slug=load.slug)
    pk = None
    default_carrier = Company.objects.filter(company_mc=load_carr.load_carrier)

    for i in default_carrier:
        pk = i.pk
    company = get_object_or_404(Company, pk=pk)

    date = datetime.now()
    title_invoice = f'Invoice #{load.pk}-{load.seller_load_number}'

    template_path = 'pdfview/invoice_for_seller.html'
    context = {'load': load, 'company': company, 'title_invoice': title_invoice, 'date': date}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="invoice_{load.pk}-{load.seller_load_number}.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def render_pdf_invoice_for_company(request, *args, **kwargs):
    post_data = request.POST.copy()
    company = get_object_or_404(transport.models.Company, pk=post_data['broker_carrier_mc'])
    bill_to = post_data['bill_to']
    amount = post_data['amount']
    description = post_data['description']

    date = datetime.now()

    title_invoice = f'Invoice '

    template_path = 'pdfview/invoice_for_company.html'
    context = {'title_invoice': title_invoice,
               'date': date,
               'company': company,
               'bill_to': bill_to,
               'description': description,
               'amount': amount,
               }
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = f'filename="invoice_{date.strftime("%m/%d/%Y")}.pdf"'

    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def render_pdf_company_transaction(request, *args, **kwargs):
    post_data = request.POST.copy()

    company_pk = kwargs.get('company_pk')
    company = get_object_or_404(Company, pk=company_pk)
    date_now = datetime.now()
    company_transaction = CashTransaction.objects.filter(broker_carrier_mc=company_pk, executed=True,
                                                         transaction_data__range=[post_data['data_from'],
                                                                                  post_data['data_to']])\
        .order_by('transaction_data')

    get_payment = CashTransaction.objects.filter(broker_carrier_mc=company_pk, executed=True,
                                                 transaction_name=1,
                                                 transaction_data__range=[post_data['data_from'],
                                                                          post_data['data_to']]).\
        aggregate(cash_sum=Sum('cash_sum'))
    get_payment = get_payment['cash_sum']

    sent_payment = CashTransaction.objects.filter(broker_carrier_mc=company_pk, executed=True,
                                                  transaction_name=2,
                                                  transaction_data__range=[post_data['data_from'],
                                                                           post_data['data_to']]). \
        aggregate(cash_sum=Sum('cash_sum'))
    sent_payment = sent_payment['cash_sum']

    title_transaction = f"Transaction company - {company.company_name} " \
                        f"(data for {post_data['data_from']} to {post_data['data_to']})"

    template_path = 'pdfview/company_transaction.html'
    context = {'company_transaction': company_transaction,
               'company': company,
               'title_transaction': title_transaction,
               'date': date_now,
               'get_payment': get_payment,
               'sent_payment': sent_payment,
               }
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f"filename=transaction_company_{company.company_name}" \
                                      f"({post_data['data_from']} to {post_data['data_to']}).pdf"
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
        html, dest=response)
    # if error then show some funny view
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response