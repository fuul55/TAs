from django.contrib import admin
from django.urls import path

from .templatetags.transport_tags import *
from .views import *

admin.site.site_header = "TAS Admin"
admin.site.site_title = "TAS Admin Portal"
admin.site.index_title = "Welcome to TAS Researcher Portal"

urlpatterns = [
    path('', index, name='home'),
    path('add_doc/', add_doc, name='add_doc'),
    path('mytask/', mytask, name='mytask'),
    path('load_list/', load_list, name='load_list'),
    path('finance/', finance, name='finance'),
    path('finance/to_pay', to_pay, name='to_pay'),
    path('finance/payment_expected', payment_expected, name='payment_expected'),
    path('finance/show_info_pay/<int:to_pay_id>/', show_info_pay, name='show_info_pay'),
    path('finance/to_pay_save/<int:to_pay_id>/', to_pay_save, name='to_pay_save'),
    path('finance/company_transaction/<str:company_pk>/', company_transaction, name='company_transaction'),
    path('finance/add_transaction_company_save/<int:company_pk>/',
         add_transaction_company_save, name='add_transaction_company_save'),
    path('setting/', setting, name='setting'),
    path('add_holding_company/', add_holding_company, name='add_holding_company'),
    path('setting/default_set_company/', default_set_company, name='default_set_company'),
    path('login_u/', LoginUser.as_view(), name='login_u'),
    path('logout/', logout_user, name='logout'),
    path('load/<slug:load_slug>/', show_load, name='load'),
    path('company_list/', company_list, name='company_list'),
    path('company_save/<int:pk>/', company_save, name='company_save'),
    path('show_user_list/', show_user_list, name='show_user_list'),
    path('add_user/', add_user, name='add_user'),
    path('show_user/<slug:username>/', show_user, name='show_user'),
    path('change_user_password/<slug:username>/', change_user_password, name='change_user_password'),
    path('show_company/<int:pk>/', show_company, name='show_company'),
    path('load/set_company_load/<slug:load_slug>/', set_company_load, name='set_company_load'),
    path('load/set_user/<slug:load_slug>/', set_user, name='set_user'),
    path('load/set_status/<slug:load_slug>/', set_status, name='set_status'),
    path('seller_load/<int:seller_id>/', show_seller_load, name='seller_load'),
    path('tags/seller_load_save/<int:s_load_id>', seller_load_save, name='seller_load_save'),
    path('tags/show_load_info', show_load_info, name='show_load_info'),
    path('tags/seller_documents', seller_documents, name='seller_documents'),
    path('tags/seller_documents/<int:doc_id>', delete_seller_doc, name='delete_seller_doc'),
    path('tags/buyer_load_info', buyer_load_info, name='buyer_load_info'),
    path('tags/buyer_documents', buyer_documents, name='buyer_documents'),
    path('tags/buyer_documents/<int:doc_id>', delete_buyer_doc, name='delete_buyer_doc'),
    path('tags/seller_load_add', seller_load_add, name='seller_load_add'),
    path('tags/buyer_load_edit', buyer_load_edit, name='buyer_load_edit'),
    path('tags/cash_transaction_seller_add/<slug:pk_load>/', cash_transaction_seller_add,
         name='cash_transaction_seller_add'),
    path('tags/cash_transaction_buyer_add/<slug:buyer_pk>/', cash_transaction_buyer_add,
         name='cash_transaction_buyer_add'),
    path('tags/delete_seller_payment/<int:doc_id>', delete_seller_payment, name='delete_seller_payment'),
    path('tags/delete_company_payment/<int:doc_id>', delete_company_payment, name='delete_company_payment'),

]