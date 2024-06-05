from db import get_db_handle as db
from selenium import webdriver
from chromedriver_py import binary_path
import time
import datetime
      
options = webdriver.ChromeOptions()
options.add_argument('incognito')
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-software-rasterizer')
options.add_argument('user-agent=User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36')        

service = webdriver.ChromeService(executable_path=binary_path)
driver = webdriver.Chrome(service=service, options=options)

driver.get('https://web.whatsapp.com/')

URL = 'https://web.whatsapp.com/'
AUTH_BUTTON = "//span[@tabindex=0]"
AUTH_NUMBER_INPUT = "//input[@aria-required='true']"
AUTH_CODE = "//div[@aria-details='link-device-phone-number-code-screen-instructions']"
AUTH_CODE_ATTRIBUTE = 'data-link-code'
SEARCH_INPUT = "//div[@contenteditable='true'][@data-tab='3']"


def get_command():
    col = db()['driver_commands']
    doc = col.find_one()
    if not doc == None:
        col.delete_one(doc)
    return doc

def get_message():
    return None

def get_instances():
    col = db()['instances']
    doc = col.find()
    return doc


def create_instance(instance):
    driver.switch_to.new_window('window')
    driver.get(URL)
    window_id = driver.current_window_handle
    col = db()['instances']
    query = {'instance': instance}
    value = {'$set': {
        'window_id': window_id,
    }}
    x = col.update_one(query, value)

def auth(instance, authnumber):
    col = db()['instances']
    query = {'instance': instance}
    doc = col.find_one(query)
    driver.switch_to.window(doc['window_id'])

    driver.find_element("xpath", AUTH_BUTTON).click()
    time.sleep(2)
    authnumber = driver.find_element("xpath", AUTH_NUMBER_INPUT)
    authnumber.send_keys(authnumber)
    authnumber.send_keys(webdriver.common.keys.Keys.RETURN)
    time.sleep(1)

    authcode = driver.find_element("xpath", AUTH_CODE)
    authcode = authcode.get_attribute(AUTH_CODE_ATTRIBUTE)
    value = {"$set": {
        'authcode': authcode,
        'auth_start': datetime.datetime.today(),
        'status': 'auth_process',
        }}
    x = col.update_one(query, value)
    return None

def status_update(instance, status):
    col = db()['instances']
    query = {'instance': instance}
    x = col.update_one(query, {"$set": {"status": status}})



while True:
    command = get_command()
    if not command == None:

        if command['command_name'] == 'create_instance':
            create_instance(command['instance'])
        if command['command_name'] == 'auth':
            auth(command['instance'], command['authnumber'])

    message = get_message()
    if not message == None:
        x = 1

    for i in get_instances():
        driver.switch_to.window(i['window_id'])
        
        if driver.current_url == URL:
            try:
                search_input = driver.find_element("xpath", SEARCH_INPUT)
                status = 'auth'
            except:
                status = 'noauth'
        else:
            status = 'wrongurl'

        if i['status'] == 'auth_process' and datetime.datetime.today()-i['auth-start']>20:
            driver.get(URL)

            col = db()['instances']
            query = {'instance': i['instance']}
            value = {"$set": {
                'authcode': '',
                'auth_start': '',
            }}
            x = col.update_one(query, value)
            status = 'noauth'

        status_update(i['instance'], status)

    time.sleep(2)

"""
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
"""