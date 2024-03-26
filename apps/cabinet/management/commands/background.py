from db import get_db_handle as db
from selenium import webdriver


while True:
    col = db()['instances']
    query = {}

    doc = col.find(query, {'_id': 0, 'instance': 1})

    for i in doc:
        status = ''
        try:
            if globals()['driver' + str(i['instance'])].current_url == 'https://web.whatsapp.com/':
                try:
                    qr = globals()['driver' + str(i['instance'])].find_element(webdriver.common.by.By.CLASS_NAME, "_19vUU")
                    status = 'noauth'
                except:
                    try:
                        search_input = globals()['driver' + str(i['instance'])].find_element("xpath", "//div[@contenteditable='true'][@data-tab='3']")
                        status = 'auth'
                    except:
                        pass
            else:
                status = 'nodriver'
        except:
            pass

        query = {'instance': i['instance']}
        value = {"$set": {"status": status}}
        x = col.update_one(query, value)