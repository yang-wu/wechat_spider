#coding=utf-8
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import json
import random
import requests
import re
import io
from bs4 import BeautifulSoup
import sys
reload(sys)

sys.setdefaultencoding('utf8')
account_name = "xxxx@163.com"     #公众号账号
password = "xxxxxx"               #公众号密码
newsapi = "http://192.168.108.183:8088/news/add"   #公众号新闻入库接口


def wechat_login():

    print("启动浏览器，打开微信公众号登录界面")
    driver = webdriver.Firefox(executable_path='/opt/wechat-spider/geckodriver')
    driver.get("https://mp.weixin.qq.com/")
    time.sleep(2)
    print("正在输入微信公众号登录账号和密码......")
    # 清空账号框中的内容
    driver.find_element_by_name("account").clear()

    driver.find_element_by_name("account").send_keys(account_name)
    time.sleep(1)
    driver.find_element_by_name("password").clear()
    driver.find_element_by_name("password").send_keys(password)
    time.sleep(1)
    # 在自动输完密码之后需要手动点一下记住我
    print("请在登录界面点击:记住账号")
    driver.find_element_by_class_name("frm_checkbox_label").click()
    time.sleep(5)
    # 自动点击登录按钮进行登录
    driver.find_element_by_class_name("btn_login").click()
    time.sleep(5)
    print(driver.current_url)
    # 拿手机扫二维码！
    print("请拿手机扫码二维码登录公众号")
    time.sleep(20)
    print("登录成功")
    # 获取cookies
    cookie_items = driver.get_cookies()
    cookies = {}
    # 获取到的cookies是列表形式，将cookies转成json形式并存入本地名为cookie的文本中
    for cookie_item in cookie_items:
        cookies[cookie_item['name']] = cookie_item['value']
    cookie_str = json.dumps(cookies)
    with io.open('cookie.txt', 'w+', encoding='utf-8') as f:
        f.write(u'{}\n'.format(cookie_str))
    print("cookies信息已保存到本地")
    driver.quit()

# 爬取微信公众号文章，并存在本地文本中


def get_content(query):
    # query为要爬取的公众号名称
    # 公众号主页
    url = 'https://mp.weixin.qq.com'

    # 设置headers
    header = {
        "HOST": "mp.weixin.qq.com",
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"

    }
    from requests.packages import urllib3
    urllib3.disable_warnings()  # 关闭警告

    # 读取上一步获取到的cookies
    with io.open('cookie.txt', 'r', encoding='utf-8') as f:
        cookie = f.read()
    cookies = json.loads(cookie)
    # 增加重试连接次数
    session = requests.Session()
    session.keep_alive = False
    # 增加重试连接次数
    session.adapters.DEFAULT_RETRIES = 511
    time.sleep(5)
    # 登录之后的微信公众号首页url变化为：https://mp.weixin.qq.com/cgi-bin/home?t=home/index&lang=zh_CN&token=1849751598，从这里获取token信息
    response = session.get(url=url, cookies=cookies, verify=False)
    token = re.findall(r'token=(\d+)', str(response.url))[0]
    time.sleep(2)
    # 搜索微信公众号的接口地址
    search_url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
    # 搜索微信公众号接口需要传入的参数，有三个变量：微信公众号token、随机数random、搜索的微信公众号名字
    query_id = {
        'action': 'search_biz',
        'token': token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'query': query,
        'begin': '0',
        'count': '5'
    }
    # 打开搜索微信公众号接口地址，需要传入相关参数信息如：cookies、params、headers
    search_response = session.get(
        search_url,
        cookies=cookies,
        headers=header,
        params=query_id)
    # 取搜索结果中的第一个公众号

    lists = search_response.json().get('list')[0]
    # 获取这个公众号的fakeid，后面爬取公众号文章需要此字段
    fakeid = lists.get('fakeid')

    # 微信公众号文章接口地址
    appmsg_url = 'https://mp.weixin.qq.com/cgi-bin/appmsg?'
    # 搜索文章需要传入几个参数：登录的公众号token、要爬取文章的公众号fakeid、随机数random
    query_id_data = {
        'token': token,
        'lang': 'zh_CN',
        'f': 'json',
        'ajax': '1',
        'random': random.random(),
        'action': 'list_ex',
        'begin': '0',  # 不同页，此参数变化，变化规则为每页加5
        'count': '5',
        'query': '',
        'fakeid': fakeid,
        'type': '9'
    }
    # 打开搜索的微信公众号文章列表页
        appmsg_response = session.get(
        appmsg_url,
        cookies=cookies,
        headers=header,
        params=query_id_data)
    # 获取文章总数
    max_num = appmsg_response.json().get('app_msg_cnt')
    # 每页至少有5条，获取文章总的页数，爬取时需要分页爬
    num = int(int(max_num) / 5)
    # 起始页begin参数，往后每页加5
    begin = 0
    seq = 0
    while num + 1 > 0:
        query_id_data = {
            'token': token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': random.random(),
            'action': 'list_ex',
            'begin': '{}'.format(str(begin)),
            'count': '5',
            'query': '',
            'fakeid': fakeid,
            'type': '9'
        }
        print('now page at：--------------', begin)
        time.sleep(5)

        # 获取每一页文章的标题和链接地址，并写入本地文本中
        query_fakeid_response = requests.get(
            appmsg_url,
            cookies=cookies,
            headers=header,
            params=query_id_data)
        fakeid_list = query_fakeid_response.json().get('app_msg_list')
        if fakeid_list:
            for item in fakeid_list:
                title = item.get('title')
                create_time = item.get('create_time')
                source = "新钛云服"
                digest = item.get("digest")
                cover = item.get('cover')
                content_link = item.get('link')
                resp = session.get(url=content_link, verify=False)
                html_page = resp.text
                soup = BeautifulSoup(html_page, 'lxml')
                meta_content = soup.find(id="meta_content")
                if meta_content and meta_content.find("span", class_="rich_media_meta rich_media_meta_text"):
                    author_html = meta_content.find("span", class_="rich_media_meta rich_media_meta_text")
                    author = author_html.text.strip()
                else:
                    author = "新钛云服"
                js_content = soup.find(id="js_content")
                img_list = js_content.find_all("img")
                for img in img_list:
                    if not img.has_attr('src'):
                        img.attrs["src"] = img.attrs["data-src"]
                content = js_content.prettify()
                body = {
                    "author": author,
                    "create_time": create_time,
                    "comefrom": source,
                    "title": title,
                    "content": content,
                    "type": "2" ,
                    "summary": digest,
                    "img_url": cover
                   }
                create_news(body)
        num -= 1
        begin = int(begin)
        begin += 5

def create_news(body):
    print(body)
    resp = requests.post(url=newsapi, data=body)

if __name__ == '__main__':

    # 登录微信公众号，获取登录之后的cookies信息，并保存到本地文本中
    wechat_login()
    query = "newtyun"
    print("开始爬取公众号：" + query)
    get_content(query)
    print("爬取完成")
