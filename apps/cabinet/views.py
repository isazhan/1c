from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.http import HttpResponse, JsonResponse
from db import get_db_handle as db
from selenium import webdriver
import time
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
from .models import CustomUser
import json
import threading


@csrf_exempt
def sign_up(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        user = CustomUser.objects.create_user(email=email, password=password)
        login(request, user)
        return redirect('cabinet')
    else:
        return render(request, 'cabinet/signup.html')


def login_user(request):
    if request.method == 'POST':
        email = request.POST['username']
        password = request.POST['password']
        user = authenticate(email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('cabinet')
        else:
            return render(request, 'cabinet/login.html')
    else:
        return render(request, 'cabinet/login.html')
    

def logout_user(request):
    logout(request)
    return render(request, 'main/index.html')
    
    
@login_required
def cabinet(request):
    return render(request, 'cabinet/cabinet.html')


@login_required
def instances(request):
    col = db()['instances']
    query = {'user': request.user.email}
    doc = col.find(query)
    context = {'instances': doc}
    template = loader.get_template('cabinet/instances.html')    
    return HttpResponse(template.render(context, request))


@login_required
@csrf_exempt
def create_instance(request):
    if request.method == 'POST':
        import secrets
        import datetime
        col = db()['instances']
        doc = col.find({}, {'_id': 0, 'instance': 1}).sort('_id', -1).limit(1)
        try:
            instance = doc[0]['instance'] + 1
        except:
            instance = 1000000
        data = {
            'instance': instance,
            'create_time': datetime.datetime.today(),
            'token': secrets.token_urlsafe(),
            'user': request.user.email,
            'qr': '',
            'status': '',
            'authcode': '',
        }
        x = col.insert_one(data)

        col = db()['driver_commands']
        data = {
            'command_name': 'create_instance',
            'instance': instance,
        }
        x = col.insert_one(data)


@csrf_exempt
def create_driver(request, instance=0):
    if request.method == 'POST':
        data = json.loads(request.body)
        instance = int(data['instance'])
        col = db()['driver_commands']
        data = {
            'command_name': 'create_instance',
            'instance': instance,
        }
        x = col.insert_one(data)


@login_required
@csrf_exempt
def auth_instance(request):
    print(request)
    if request.method == 'POST':
        print(request.POST['instance'])
        instance = int(request.POST['instance'])
        authnumber = request.POST['authnumber']
        
        col = db()['driver_commands']
        data = {
            'command_name': 'auth',
            'instance': instance,
            'authnumber': authnumber,
        }
        x = col.insert_one(data)

        while True:
            doc = db()['instances'].find_one({'instance': instance})
            print(doc)
            if not doc['authcode'] == '':
                break
            time.sleep(1)
        return HttpResponse(doc['authcode'])


def status_update(instance, status):
    col = db()['instances']
    query = {'instance': instance}
    x = col.update_one(query, {"$set": {"status": status}})


def instance(request, inst_number):
    col = db()['instances']
    query = {'instance': inst_number}
    doc = col.find(query)
    status = doc[0]['status']
    context = {
        'instance': inst_number,
        'status': status,
        }
    template = loader.get_template('cabinet/instance.html')
    return HttpResponse(template.render(context, request))


@csrf_exempt
def get_qr(request):
    if request.method == 'GET':
        instance = int(request.GET['instance'])
        col = db()['instances']
        query = {'instance': instance}
        doc = col.find_one(query, {'_id': 0, 'qr': 1})
        return HttpResponse(doc['qr'])


@csrf_exempt
def check_auth(request):
    if request.method == 'GET':
        instance = int(request.GET['instance'])
        col = db()['instances']
        query = {'instance': instance}
        while True:
            doc = col.find_one(query)
            if doc['status'] == 'auth':
                break
        return HttpResponse('reload')


def one_message(request):
    col = db()['instances']
    query = {'user': request.user.email, 'status': 'auth'}
    doc = col.find(query)
    context = {'instances': doc}
    template = loader.get_template('cabinet/one_message.html')
    return HttpResponse(template.render(context, request))


def few_messages(request):
    col = db()['instances']
    query = {'user': request.user.email, 'status': 'auth'}
    doc = col.find(query)
    context = {'instances': doc}
    template = loader.get_template('cabinet/few_messages.html')
    return HttpResponse(template.render(context, request))


def message_order(request):
    if request.method == 'POST':
        instance = int(request.POST['instance'])
        telnumbers = str(request.POST['telnumbers'])
        telnumbers = list(telnumbers.split(','))
        message = str(request.POST['message'])
        wait = int(request.POST['wait'])
        data = []
        for telnumber in telnumbers:
            body = {
                'instance': instance,
                'telnumber': telnumber,
                'message': message,
                'wait': wait,
            }
            data.append(body)

        col = db()['messages']
        x = col.insert_many(data)
        return redirect('cabinet')
