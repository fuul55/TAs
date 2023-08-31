from django.urls import path
from .views import render_pdf_view, render_pdf_invoice_for_seller, render_pdf_company_transaction, \
    render_pdf_invoice_for_company, export_load_csv

app_name = 'pdfview'

urlpatterns = [
    path('rate_confirmation/<slug>/', render_pdf_view, name='pdf-view_rate_confirmation'),
    path('invoice/<int:seller_pk>/', render_pdf_invoice_for_seller, name='render_pdf_invoice_for_seller'),
    path('company_transaction/<int:company_pk>/', render_pdf_company_transaction, name='render_pdf_company_transaction'),
    path('company_invoice/', render_pdf_invoice_for_company, name='render_pdf_invoice_for_company'),
    path('export_load_csv/', export_load_csv, name='export_load_csv'),
]
