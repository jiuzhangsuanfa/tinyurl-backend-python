import json

from django.shortcuts import render
from django.http import HttpResponse
from datetime import datetime, timedelta

from conversion.models import Long2Short
from .models import Visit


def history(request):
    # ip_address = request.headers['Referer']
    ip_address = "192.168.33.11"
    url_history = Long2Short.objects.filter(ip_address=ip_address).order_by("-create_date")[:5].values()
    rows = []
    for i in url_history:
        i["create_date"] = i["create_date"].strftime("%Y-%m-%d %H:%M:%S")
        rows.append(i)
    res = {
        "data": rows
    }

    response = HttpResponse(json.dumps(res))

    return response


def visit_info(request):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    week_ago_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    temp = Visit.objects.all().values()
    url_visit_info = Visit.objects.filter(create_date__gt=week_ago_time).filter(create_date__lt=current_time).values()
    pass



