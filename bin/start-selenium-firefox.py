#!/usr/bin/env python3

import json
import os
import sys
import time
from urllib import parse as urlparse

import requests
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import exceptions

def do_fake(browser):
    browser.get('file:///drivers/fake/index.html')

def do_ilo(browser):
    url = os.environ.get('BMC_URL')
    username = os.environ.get('BMC_USERNAME')
    password = os.environ.get('BMC_PASSWORD')
    verify = os.environ.get('BMC_VERIFY', 'true').lower() == 'true'
    login_url = f'{url}redfish/v1/Sessions/'
    console_url = f'{url}irc.html'

    def interceptor(request):
        print(f'request {request}')

    browser.request_interceptor = interceptor

    # Load the BMC login page
    browser.get(url)

    # Transfer the browser response cookies to the request
    jar = requests.cookies.RequestsCookieJar()
    for cookie in browser.get_cookies():
        cname = cookie["name"]
        cvalue = urlparse.unquote(cookie["value"])

        print(f'Setting cookie {cname}={cvalue}')
        jar.set(cname, cvalue)

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': f'{url}html/login.html',
        'X-Client-Type': 'Browser',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': url,
        'Host': urlparse.urlparse(url).netloc
    }
    r = requests.post(login_url, verify=verify, cookies=jar, headers=headers,
                      json={'UserName': username, 'Password': password})
    print(r.status_code)
    print(r.cookies.get('sessionKey'))
    print(r.headers)
    print(json.dumps(r.json(), indent=2))

    if 'Location' in r.headers:
        location = urlparse.quote(urlparse.urlparse(r.headers['Location']).path)
        print(f'Location={location}')
        browser.add_cookie({'name': 'Location', 'value': location})

    if 'X-Auth-Token' in r.headers:
        token = r.headers['X-Auth-Token']
        print(f'sessionKey={token}')
        browser.add_cookie({'name': 'sessionKey', 'value': token})

    browser.get(console_url)


    # # wait for username element
    # try:
    #     myElem = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, 'password')))
    # except exceptions.TimeoutException:
    #     print("Loading took too much time!")

    # browser.find_element(By.ID, value="username").send_keys(username)
    # browser.find_element(By.ID, value="password").send_keys(password)
    # browser.find_element(By.ID, "login-form__submit").click()

    # # wait for ircFrame
    # # browser.get(f'{url}/irc.html')

def start_browser():
    opts = webdriver.FirefoxOptions()
    opts.enable_bidi = True
    if 'DISPLAY_WIDTH' in os.environ:
        opts.add_argument('-width')
        opts.add_argument(os.environ['DISPLAY_WIDTH'])
    if 'DISPLAY_HEIGHT' in os.environ:
        opts.add_argument('-height')
        opts.add_argument(os.environ['DISPLAY_HEIGHT'])
    if 'FIREFOX_ARGS' in os.environ:
        for arg in os.environ['FIREFOX_ARGS'].split(' '):
            opts.add_argument(arg)

    browser = webdriver.Firefox(options=opts)
    browser.script.add_console_message_handler(print)
    return browser

driver_entrypoints = {
    'fake': do_fake,
    'ilo-graphical': do_ilo
}

def main():
    browser = start_browser()
    driver_func = driver_entrypoints.get(os.environ.get('DRIVER'))
    if driver_func:
        driver_func(browser)

if __name__ == '__main__':
    sys.exit(main())