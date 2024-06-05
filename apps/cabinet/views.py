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
            'authnumber': '',
            'authcode': '',
        }
        x = col.insert_one(data)
        #z = requests.post(create_driver, json={'instance': instance})
        #globals()['thread' + str(instance)] = threading.Thread(target=create_driver(request, instance))
        #globals()['thread' + str(instance)].start()
        #request.method = 'GET'
        #create_driver(request, instance)
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
    globals()['thread' + str(instance)] = threading.Thread(target=manage_driver(instance))
    globals()['thread' + str(instance)].start()



def manage_driver(instance):
    #if request.method == 'POST':        
        #data = json.loads(request.body)
        #instance = int(data['instance'])        
        options = webdriver.ChromeOptions()
        options.add_argument('incognito')
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('user-agent=User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36')        

        # for linux:
        #service = webdriver.ChromeService(executable_path=r'/usr/bin/chromedriver')
        #driver = webdriver.Chrome(service=service ,options=options)
        # for windows:
        #driver = webdriver.Chrome(options=options)
        from chromedriver_py import binary_path
        service = webdriver.ChromeService(executable_path=binary_path)
        driver = webdriver.Chrome(service=service, options=options)

        driver.get('https://web.whatsapp.com/')

        col = db()['instances']
        query = {'instance': instance}
        value = {'$set': {
            'session': driver.session_id,
            'executor': driver.command_executor._url,
            }}
        #x = col.update_one(query, value)
        i = 0
        while True:
            status = ''
            try:
                if driver.current_url == 'https://web.whatsapp.com/':
                    try:
                        search_input = driver.find_element("xpath", "//div[@contenteditable='true'][@data-tab='3']")
                        status = 'auth'
                        value = {"$set": {"authcode": '', "authnumber": ''}}
                        x = col.update_one(query, value)
                        i = 0
                        try:
                            col = db()['messages']
                            doc = col.find_one(query)
                                
                            search_input.send_keys(doc['telnumber'])
                            time.sleep(2)
                            search_input.send_keys(webdriver.common.keys.Keys.RETURN)
                            time.sleep(2)
                            try:
                                chat = driver.find_element("xpath", "//div[@class='_ajx_']")                            
                                message_input = driver.find_element("xpath", "//div[@contenteditable='true'][@data-tab='10']")
                                message_input.send_keys(doc['message'])
                                message_input.send_keys(webdriver.common.keys.Keys.RETURN)
                                time.sleep(2)
                            except:
                                pass
                            print('test1')
                            webdriver.ActionChains(driver).send_keys(webdriver.common.keys.Keys.ESCAPE).perform()
                            print('test2')
                            #driver.find_element("xpath", "//button[@class='_ah_y']").click()
                            print('test3')
                            time.sleep(doc['wait'])
                            print(doc['wait'])
                            print('test4')
                            x = col.delete_one({'_id': doc['_id']})
                            print('test5')
                        except:
                            pass
                    except:
                        try:
                            #qr = driver.find_element(webdriver.common.by.By.CLASS_NAME, "_akau")
                            #qr = qr.get_attribute("data-ref")
                            #value = {"$set": {"qr": qr}}
                            #x = col.update_one(query, value)
                            status = 'noauth'
                            doc = db()['instances'].find_one({'instance': instance})
                            if not doc['authnumber']=='':
                                try:
                                    driver.find_element("xpath", "//span[@tabindex=0]").click()
                                    time.sleep(2)
                                    authnumber = driver.find_element("xpath", "//input[@aria-required='true']")
                                    authnumber.send_keys(doc['authnumber'])
                                    authnumber.send_keys(webdriver.common.keys.Keys.RETURN)
                                    time.sleep(1)
                                except:
                                    pass
                                authcode = driver.find_element("xpath", "//div[@aria-details='link-device-phone-number-code-screen-instructions']")
                                authcode = authcode.get_attribute('data-link-code')
                                value = {"$set": {"authcode": authcode}}
                                x = col.update_one(query, value)
                                i+=1
                                print(i)
                                if i==20:
                                    value = {"$set": {"authcode": '', "authnumber": ''}}
                                    x = col.update_one(query, value)
                                    driver.get('https://web.whatsapp.com/')
                                    i = 0
                        except:
                            pass
                else:
                    status = 'wrongurl'
            except:
                status = 'nodriver'

            print(status)
            status_update(instance, status)
            time.sleep(2)
            #print(driver.current_url)


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
            if doc['status'] == 'auth' or doc['authnumber'] == '':
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
