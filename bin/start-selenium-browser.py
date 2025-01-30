#!/usr/bin/env python3

import json
import os
import sys
import time
from urllib import parse as urlparse

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import exceptions

class BaseApp:

    @property
    def url(self):
        pass

    def start(self, driver):
        pass

class FakeApp(BaseApp):

    @property
    def url(self):
        return 'file:///drivers/fake/index.html'

class BMCApp(BaseApp):

    @property
    def url(self):
        return os.environ.get('BMC_URL')

    def disable_right_click(self, driver):
        # disable right-click menu
        driver.execute_script('window.addEventListener("contextmenu", function(e) { e.preventDefault(); })')

class IloApp(BMCApp):

    def start(self, driver):
        url = self.url
        username = os.environ.get('BMC_USERNAME')
        password = os.environ.get('BMC_PASSWORD')
        console_url = f'{url}irc.html'

        self.disable_right_click(driver)
        # full screen content is shown in an embedded iframe
        iframe = driver.find_element(By.ID, "appFrame")
        driver.switch_to.frame(iframe)

        # wait for the username field to be enabled then perform login
        username_field = driver.find_element(By.ID, value="username")
        wait = WebDriverWait(
            driver, timeout=5, poll_frequency=.2,
            ignored_exceptions=[exceptions.ElementNotInteractableException])
        wait.until(lambda d : username_field.send_keys(username) or True)

        driver.find_element(By.ID, value="password").send_keys(password)
        driver.find_element(By.ID, value="login-form__submit").click()

        # wait for <body id="app-container"> to exist, which indicates
        # the login form has submitted and session cookies are now set
        wait = WebDriverWait(
            driver, timeout=10, poll_frequency=.2,
            ignored_exceptions=[exceptions.NoSuchElementException])
        wait.until(lambda d : driver.find_element(By.ID, value="app-container") or True)

        # load the actual console
        driver.get(console_url)

        self.disable_right_click(driver)

class SupermicroApp(BMCApp):

    def start(self, driver):
        username = os.environ.get('BMC_USERNAME')
        password = os.environ.get('BMC_PASSWORD')

        # populate login and submit
        driver.find_element(By.NAME, value="name").send_keys(username)
        driver.find_element(By.ID, value="pwd").send_keys(password)
        driver.find_element(By.ID, value="login_word").click()

        # navigate down some iframes
        iframe = driver.find_element(By.ID, "TOPMENU")
        driver.switch_to.frame(iframe)

        iframe = driver.find_element(By.ID, "frame_main")
        driver.switch_to.frame(iframe)


        wait = WebDriverWait(
            driver, timeout=30, poll_frequency=.2,
            ignored_exceptions=[exceptions.NoSuchElementException,
                                exceptions.ElementNotInteractableException])
        wait.until(lambda d : driver.find_element(By.ID, value="img1") or True)

        # launch the console by waiting for the console preview image to be
        # loaded and clickable
        def snapshot_wait(d):
            try:
                img1 = driver.find_element(By.ID, value="img1")
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

        wait = WebDriverWait(driver, timeout=30, poll_frequency=1)
        wait.until(snapshot_wait)

        # self.disable_right_click(driver)


def start_driver(url=None):
    print(f'starting app with url {url}')
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

app_classes = {
    'fake': FakeApp,
    'ilo-graphical': IloApp,
    'supermicro-graphical': SupermicroApp,
}

def main():
    app_name = os.environ.get('APP')
    app_class = app_classes.get(app_name)
    if not app_class:
        raise Exception(f'Unknown app {app_name}')

    app = app_class()

    driver = start_driver(url=app.url)
    print(f'got driver {driver}')

    print(f'Running app {app_name}')
    app.start(driver)
    while True:
        time.sleep(10)

if __name__ == '__main__':
    sys.exit(main())