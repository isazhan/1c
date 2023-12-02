from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.http import HttpResponse
from db import get_db_handle as db
from selenium import webdriver
import time
from django.views.decorators.csrf import csrf_exempt


def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
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
    query = {'user': request.user.username}
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
        'instance' : instance,
        'token': secrets.token_urlsafe(),
        'user': request.user.username,
    }
    x = col.insert_one(data)
    return redirect('instances')

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
    open_driver(request, inst_number)
    context = {}
    template = loader.get_template('cabinet/instance.html')
    return HttpResponse(template.render(context, request))


def open_driver(request, inst_number):
    options = webdriver.ChromeOptions()
    options.add_argument('--user-data-dir=..//instances/'+str(inst_number))
    options.add_experimental_option('detach', True)
    driver = webdriver.Chrome(options=options)
    driver.get('https://web.whatsapp.com/')

    qr = None
    for i in range(60):
        try:
            qr_code_element = driver.find_element(webdriver.common.by.By.CLASS_NAME, "_19vUU")
            qr = qr_code_element.get_attribute("data-ref")
            col = db()['instances']
            doc = col[inst_number]
            doc['qr'] = qr
        except:
            pass
        time.sleep(1)

    driver.close()


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