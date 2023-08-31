from django import forms
import json

import requests
from django.shortcuts import get_object_or_404

from transport.models import Load


class MyDateInput(forms.DateInput):
    input_type = 'date'
    format = '%m-%d-%Y'


def get_mc_info(mc_number):
    len_mc = len(str(mc_number))
    ms_n = 7
    i = '0'
    len_correct = ms_n - int(len_mc)
    new_str = i * len_correct
    mc = new_str + str(mc_number)

    # mc = mc_number
    wb_key = 'b19df8c62ce824d3134984c27d38e8276a43ecf6'

    string_as = requests.get(f'https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{mc}?webKey={wb_key}')
    if string_as.status_code == 200:
        obj = json.loads(string_as.text)
        if obj['content']:
            for i in obj['content']:
                info_company_list = i['carrier']
            return info_company_list

    info_company_list = {'dotNumber': 'no info',
                         'legalName': 'no info',
                         'phyCity': '',
                         'phyCountry': '',
                         'phyState': '',
                         'phyStreet': 'no info',
                         'phyZipcode': '',
                         }

    return info_company_list
