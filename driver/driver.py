from db import get_db_handle as db
from selenium import webdriver
from chromedriver_py import binary_path
import time
      
options = webdriver.ChromeOptions()
options.add_argument('incognito')
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-software-rasterizer')
options.add_argument('user-agent=User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36')


chrome_prefs = {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2
}
options.add_experimental_option("prefs", chrome_prefs)



service = webdriver.ChromeService(executable_path=binary_path)
driver = webdriver.Chrome(service=service, options=options)

driver.get('https://web.whatsapp.com/')

URL = 'https://web.whatsapp.com/'
AUTH_BUTTON = "//span[@tabindex=0]"
AUTH_NUMBER_INPUT = "//input[@aria-required='true']"
AUTH_CODE = "//div[@aria-details='link-device-phone-number-code-screen-instructions']"
AUTH_CODE_ATTRIBUTE = 'data-link-code'
SEARCH_INPUT = "//div[@contenteditable='true'][@data-tab='3']"
MESSAGE_INPUT = "//div[@contenteditable='true'][@data-tab='10']"


def get_command():
    col = db()['driver_commands']
    doc = col.find_one()
    if not doc == None:
        col.delete_one(doc)
    return doc

def get_message():
    col = db()['messages']
    doc = col.find_one()
    if not doc == None:
        col.delete_one(doc)
    return doc

def get_instances():
    col = db()['instances']
    doc = col.find()
    return doc

def get_window(instance):
    col = db()['instances']
    query = {'instance': instance}
    doc = col.find_one(query)
    return doc['window_id']


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
    window = get_window(instance)
    driver.switch_to.window(window)

    driver.find_element("xpath", AUTH_BUTTON).click()
    time.sleep(2)
    authnumber_input = driver.find_element("xpath", AUTH_NUMBER_INPUT)
    authnumber_input.send_keys(authnumber)
    authnumber_input.send_keys(webdriver.common.keys.Keys.RETURN)
    time.sleep(2)

    authcode = driver.find_element("xpath", AUTH_CODE)
    authcode = authcode.get_attribute(AUTH_CODE_ATTRIBUTE)
    value = {"$set": {
        'authcode': authcode,
        'auth_start': time.time(),
        'status': 'auth_process',
        }}
    col = db()['instances']
    query = {'instance': instance}
    x = col.update_one(query, value)
    return None

def status_update(instance, status):
    col = db()['instances']
    query = {'instance': instance}
    x = col.update_one(query, {"$set": {"status": status}})


def send_message(instance, telnumber, message):
    window = get_window(instance)
    driver.switch_to.window(window)
    search_input = driver.find_element("xpath", SEARCH_INPUT)
    search_input.send_keys(telnumber)
    time.sleep(2)
    search_input.send_keys(webdriver.common.keys.Keys.RETURN)
    time.sleep(2)
    try:
        message_input = driver.find_element("xpath", MESSAGE_INPUT)
        message_input.send_keys(message)
        message_input.send_keys(webdriver.common.keys.Keys.RETURN)
        webdriver.ActionChains(driver).send_keys(webdriver.common.keys.Keys.ESCAPE).perform()
    except:
        pass

# Set status 'nodriver' for all instances
col = db()['instances']
value = {"$set": {
    'status': 'nodriver',
    'window_id': 'noid',
    'auth_start': '',
    'authcode': '',
    }}
x = col.update_many({}, value)

# Main While
while True:
    command = get_command()
    if not command == None:

        if command['command_name'] == 'create_instance':
            create_instance(command['instance'])
        if command['command_name'] == 'auth':
            auth(command['instance'], command['authnumber'])

    message = get_message()
    if not message == None:
        send_message(message['instance'], message['telnumber'], message['message'])

    for i in get_instances():
        try:
            driver.switch_to.window(i['window_id'])
            
            if driver.current_url == URL:
                try:
                    search_input = driver.find_element("xpath", SEARCH_INPUT)
                    status = 'auth'
                except:
                    status = 'noauth'
            else:
                status = 'wrongurl'

            if i['status'] == 'auth_process':
                status = 'auth_process'
                if time.time()-i['auth_start']>20:
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
        except:
            pass

    time.sleep(2)
