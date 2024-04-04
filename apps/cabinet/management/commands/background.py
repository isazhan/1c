from db import get_db_handle as db
from selenium import webdriver


while True:
    col = db()['instances']
    query = {}

    doc = col.find(query, {'_id': 0, 'instance': 1, 'session': 1, 'executor': 1})

    for i in doc:
        try:
            options = webdriver.ChromeOptions()
            executor = i['executor']
            driver = webdriver.Remote(command_executor=executor, options=options)
            driver.close()
            driver.session_id = i['session']
            status = ''

            try:
                if driver.current_url == 'https://web.whatsapp.com/':
                    try:
                        qr = driver.find_element(webdriver.common.by.By.CLASS_NAME, "_akau")
                        status = 'noauth'
                    except:
                        try:
                            search_input = driver.find_element("xpath", "//div[@contenteditable='true'][@data-tab='3']")
                            status = 'auth'
                        except:
                            status = 'wrongclassname'
                else:
                    status = 'wrongurl'
            except:
                status = 'nodriver'            
        except:
            status = 'nodriver'
            query = {'instance': i['instance']}
            value = {"$set": {"executor": '', 'session': ''}}
            x = col.update_one(query, value)
        query = {'instance': i['instance']}
        value = {"$set": {"status": status}}
        x = col.update_one(query, value)