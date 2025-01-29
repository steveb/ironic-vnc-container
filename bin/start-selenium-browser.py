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
    pass

def _disable_right_click(browser):
    # disable right-click menu
    browser.execute_script('window.addEventListener("contextmenu", function(e) { e.preventDefault(); })')

def do_ilo(browser):
    url = os.environ.get('BMC_URL')
    username = os.environ.get('BMC_USERNAME')
    password = os.environ.get('BMC_PASSWORD')
    console_url = f'{url}irc.html'

    _disable_right_click(browser)
    # full screen content is shown in an embedded iframe
    iframe = browser.find_element(By.ID, "appFrame")
    browser.switch_to.frame(iframe)

    # wait for the username field to be enabled then perform login
    username_field = browser.find_element(By.ID, value="username")
    wait = WebDriverWait(
        browser, timeout=5, poll_frequency=.2,
        ignored_exceptions=[exceptions.ElementNotInteractableException])
    wait.until(lambda d : username_field.send_keys(username) or True)

    browser.find_element(By.ID, value="password").send_keys(password)
    browser.find_element(By.ID, value="login-form__submit").click()

    # wait for <body id="app-container"> to exist, which indicates
    # the login form has submitted and session cookies are now set
    wait = WebDriverWait(
        browser, timeout=10, poll_frequency=.2,
        ignored_exceptions=[exceptions.NoSuchElementException])
    wait.until(lambda d : browser.find_element(By.ID, value="app-container") or True)

    # load the actual console
    browser.get(console_url)

    _disable_right_click(browser)

def do_supermicro(browser):
    url = os.environ.get('BMC_URL')
    username = os.environ.get('BMC_USERNAME')
    password = os.environ.get('BMC_PASSWORD')
    console_url = f'{url}cgi/url_redirect.cgi?url_name=man_ikvm_html5_bootstrap'

    # populate login and submit
    browser.find_element(By.NAME, value="name").send_keys(username)
    browser.find_element(By.ID, value="pwd").send_keys(password)
    browser.find_element(By.ID, value="login_word").click()

    # navigate down some iframes
    iframe = browser.find_element(By.ID, "TOPMENU")
    browser.switch_to.frame(iframe)

    iframe = browser.find_element(By.ID, "frame_main")
    browser.switch_to.frame(iframe)


    wait = WebDriverWait(
        browser, timeout=30, poll_frequency=.2,
        ignored_exceptions=[exceptions.NoSuchElementException,
                            exceptions.ElementNotInteractableException])
    wait.until(lambda d : browser.find_element(By.ID, value="img1") or True)

    # launch the console by waiting for the console preview image to be
    # loaded and clickable
    def snapshot_wait(d):
        try:
            img1 = browser.find_element(By.ID, value="img1")
        except exceptions.NoSuchElementException as e:
            print("img1 doesn't exist yet")
            return False

        if 'Snapshot' not in img1.get_attribute('src'):
            print("img1 src not a console snapshot yet")
            return False
        if not img1.get_attribute('complete') == 'true':
            print("img1 console snapshot not loaded yet")
            return False
        try:
            img1.click()
        except exceptions.ElementNotInteractableException as e:
            print("img1 not clickable yet")
            return False
        return True

    wait = WebDriverWait(browser, timeout=30, poll_frequency=1)
    wait.until(snapshot_wait)

    # _disable_right_click(browser)




def start_browser(url=None):
    opts = webdriver.ChromeOptions()
    opts.binary_location = '/usr/bin/chromium-browser'
    # opts.enable_bidi = True
    if url:
        opts.add_argument(f"--app={url}")

    verify = os.environ.get('BMC_VERIFY', 'true').lower() == 'true'
    if not verify:
        opts.add_argument("--ignore-certificate-errors")
        opts.add_argument("--ignore-ssl-errors")

    opts.add_argument("--disable-extensions")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-plugins-discovery")

    opts.add_argument("--disable-context-menu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    opts.add_argument(f"--window-position=0,0")
    opts.add_experimental_option("excludeSwitches", ['enable-automation']);
    if 'DISPLAY_WIDTH' in os.environ and 'DISPLAY_HEIGHT' in os.environ:
        width = int(os.environ['DISPLAY_WIDTH'])
        height = int(os.environ['DISPLAY_HEIGHT'])
        opts.add_argument(f"--window-size={width},{height}")
    if 'CHROME_ARGS' in os.environ:
        for arg in os.environ['CHROME_ARGS'].split(' '):
            opts.add_argument(arg)

    driver = webdriver.Chrome(options=opts)
    driver.delete_all_cookies()
    driver.set_window_position(0, 0)

    return driver

driver_entrypoints = {
    'fake': do_fake,
    'ilo-graphical': do_ilo,
    'supermicro-graphical': do_supermicro
}
driver_urls = {
    'fake': 'file:///drivers/fake/index.html',
    'ilo-graphical': os.environ.get('BMC_URL'),
    'supermicro-graphical': os.environ.get('BMC_URL')
}

def main():
    driver_name = os.environ.get('DRIVER')
    browser = start_browser(driver_urls.get(driver_name))
    print(f'got browser {browser}')
    driver_func = driver_entrypoints.get(driver_name)
    if driver_func:
        print(f'Running driver {driver_name}')
        driver_func(browser)
        while True:
            time.sleep(10)
    print('Exiting')

if __name__ == '__main__':
    sys.exit(main())