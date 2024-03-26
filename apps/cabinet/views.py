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
import asyncio

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
def create_instance(request):
    import secrets

    col = db()['instances']
    doc = col.find({}, {'_id': 0, 'instance': 1}).sort('_id', -1).limit(1)
    try:
        instance = doc[0]['instance'] + 1
    except:
        instance = 1000000
    data = {
        'instance': instance,
        'token': secrets.token_urlsafe(),
        'user': request.user.email,
        'qr': '',
        'auth': False,
    }
    x = col.insert_one(data)
    create_driver(request, instance)
    return redirect('instances')


def create_driver(request, instance):
    options = webdriver.ChromeOptions()
    options.add_argument('incognito')
    globals()['driver' + str(instance)] = webdriver.Chrome(options=options)
    globals()['driver' + str(instance)].get('https://web.whatsapp.com/')


"""
@csrf_exempt
def get_qr(request):
    print('def get_qr')
    if request.method == 'POST':
        print('post')
        options = webdriver.ChromeOptions()
        options.add_argument('--user-data-dir=./User_Data')
        options.add_experimental_option('detach', True)
        driver = webdriver.Chrome(options=options)
        driver.get('https://web.whatsapp.com/')
        return HttpResponse('ok')

    if request.method == 'GET':        
        print('get')
        qr = None
        while qr==None:
            try:
                qr_code_element = driver.find_element(webdriver.common.by.By.CLASS_NAME, "_19vUU")
                qr = qr_code_element.get_attribute("data-ref")
            except:
                pass
            time.sleep(1)
            print(qr)
        return HttpResponse(qr)
"""

def instance(request, inst_number):
    col = db()['instances']
    query = {'instance': inst_number}
    doc = col.find(query)
    auth = doc[0]['auth']
    context = {
        'instance': inst_number,
        'auth': auth,
        }
    template = loader.get_template('cabinet/instance.html')
    return HttpResponse(template.render(context, request))


@csrf_exempt
def open_driver(request):
    if request.method == 'POST':
        options = webdriver.ChromeOptions()
        #options.add_argument("--remote-debugging-port=9222")
        #options.add_argument('--allow-profiles-outside-user-dir')
        dir = os.path.dirname(settings.BASE_DIR) + '/instances/' + str(request.POST['instance'])
        options.add_argument('--user-data-dir='+dir)
        #options.add_experimental_option('detach', True)
        driver = webdriver.Chrome(options=options)
        driver.get('https://web.whatsapp.com/')
        col = db()['instances']
        query = {'instance': int(request.POST['instance'])}
        
        for i in range(30):
            try:
                qr_code_element = driver.find_element(webdriver.common.by.By.CLASS_NAME, "_19vUU")
                qr = qr_code_element.get_attribute("data-ref")
                value = {"$set": {"qr": qr}}
                x = col.update_one(query, value)
            except:
                pass
            try:
                a = driver.find_element(webdriver.common.by.By.CLASS_NAME, "_2QgSC")
                value = {"$set": {"auth": True}}
                x = col.update_one(query, value)
                break
            except:
                pass
            time.sleep(1)
        x = col.update_one(query, {"$set": {"qr": ''}})

        driver.close()
        time.sleep(5)


@csrf_exempt
def get_qr(request):
    if request.method == 'GET':
        time.sleep(2)
        col = db()['instances']
        query = {'instance': int(request.GET['instance'])}
        doc = col.find(query)
        qr = doc[0]['qr']
        return HttpResponse(qr)


@csrf_exempt
def check_auth(request):
    if request.method == 'GET':
        time.sleep(2)
        col = db()['instances']
        query = {'instance': int(request.GET['instance'])}
        doc = col.find(query)
        auth = doc[0]['auth']
        print(auth)
        print(type(auth))
        return HttpResponse(auth)
    
'''
cabinet def 1:
create instance -> open driver globals() --detach
get qr through ajax
wait login -> stop ajax and change status
wait logout -> start ajax and change status

cabinet def 2:
send message

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver1 = webdriver.Chrome(options=options)
driver1.get("https://web.whatsapp.com/")
time.sleep(5)
'''

def one_message(request):
    if request.method == 'POST':
        instance = request.POST['instance']
        telnumber = request.POST['telnumber']
        message = request.POST['message']
        send_message(request, instance, telnumber, message)
        return redirect('one_message')
    else:
        col = db()['instances']
        query = {'user': request.user.email, 'auth': True}
        doc = col.find(query)
        context = {'instances': doc}
        template = loader.get_template('cabinet/one_message.html')
        return HttpResponse(template.render(context, request))


def few_messages(request):
    if request.method == 'POST':
        instance = request.POST['instance']
        telnumbers = request.POST['telnumbers'].split(sep=',')
        message = request.POST['message']
        range = int(request.POST['range'])
        for telnumber in telnumbers:
            send_message(request, instance, telnumber, message)
            time.sleep(range)
        return redirect('few_messages')
    else:
        col = db()['instances']
        query = {'user': request.user.email, 'auth': True}
        doc = col.find(query)
        context = {'instances': doc}
        template = loader.get_template('cabinet/few_messages.html')
        return HttpResponse(template.render(context, request))


def send_message(request, instance, telnumber, message):
    options = webdriver.ChromeOptions()
    dir = os.path.dirname(settings.BASE_DIR) + '/instances/' + str(instance)
    options.add_argument('--user-data-dir='+dir)
    driver = webdriver.Chrome(options=options)
    driver.get('https://web.whatsapp.com/')
    time.sleep(10)

    search_input = driver.find_element("xpath", "//div[@contenteditable='true'][@data-tab='3']")
    search_input.send_keys(telnumber)
    time.sleep(2)

    search_input.send_keys(webdriver.common.keys.Keys.RETURN)
    time.sleep(2)

    message_input = driver.find_element("xpath", "//div[@contenteditable='true'][@data-tab='10']")

    message_input.send_keys(message)
    message_input.send_keys(webdriver.common.keys.Keys.RETURN)
    time.sleep(2)
    driver.close()
    return 'sent'