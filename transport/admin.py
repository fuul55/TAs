from django.contrib import admin

from .models import *


class LoadAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'load_buy_price', 'load_sell_price', 'stat')
    list_display_links = ('id',)
    search_fields = ('slug',)


class SellerLoadAdmin(admin.ModelAdmin):
    list_display = ('id', 'slug', 'seller_load_number', 'load_buy_price')
    list_display_links = ('id', 'seller_load_number')


class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('name',)


class DocumentNameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)


class DocSellerAdmin(admin.ModelAdmin):
    list_display = ('id', 'doc', 'documents')
    list_display_links = ('id',)


class BuyerLoadAdmin(admin.ModelAdmin):
    list_display = ('id', 'date_sold_load', 'load_sell_price')
    list_display_links = ('id',)


class DocBuyerAdmin(admin.ModelAdmin):
    list_display = ('id', 'doc', 'documents')
    list_display_links = ('id',)
    search_fields = ('load',)


class CashTransactionAdmin(admin.ModelAdmin):
    list_display = ('pk', 'slug', 'transaction_name', 'broker_carrier_mc', 'cash_sum', 'buyer_seller', 'payment_doc')
    list_display_links = ('pk',)
    list_editable = ('broker_carrier_mc',)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_display_links = ('id',)


class CompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_mc', 'company_name')
    list_display_links = ('id',)


class CompanyTypeNameAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)
    list_display_links = ('id',)


class UserCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'user_company')
    list_display_links = ('id',)


admin.site.register(SellerLoad, SellerLoadAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(DocumentName, DocumentNameAdmin)
admin.site.register(Load, LoadAdmin)
admin.site.register(DocSeller, DocSellerAdmin)
admin.site.register(BuyerLoad, BuyerLoadAdmin)
admin.site.register(DocBuyer, DocBuyerAdmin)
admin.site.register(CashTransaction, CashTransactionAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Company, CompanyAdmin)
admin.site.register(CompanyTypeName, CompanyTypeNameAdmin)
admin.site.register(UserCompany, UserCompanyAdmin)