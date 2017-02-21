#! /usr/bin/python3
# coding=utf-8

import re
import time
from datetime import date
from io import BytesIO

import requests
from bs4 import BeautifulSoup

from ocr import ocr


class UseridError(ValueError):
    pass


def str2term(datestr: str) -> tuple:
    """convert a string to parameters used by jwc system

    :type datestr: str
    """
    re_rule = re.compile(r'^(\d{4})(A|a|S|s)$')
    result = re_rule.match(datestr)
    term2num = {'s': '1', 'S': '1', 'a': '2', 'A': '2'}
    if not result:
        today = date.today()
        if 11 >= int(today.strftime('%m')) >= 7:
            yearid = str(int(today.strftime('%Y')) - 1980)
            termid = '1'
        else:
            yearid = str(int(today.strftime('%Y')) - 1981)
            termid = '2'
    else:
        yearid = str(int(result.group(1)) - 1980)
        termid = term2num[result.group(2)]
    return yearid, termid


class Query:
    def __init__(self, stuid, password):
        self.login_time = None
        self.session = requests.Session()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                   'Referer': 'https://jwc.bfsu.edu.cn'}
        self.session.headers = headers
        self.stuid, self.password = stuid, password

    @staticmethod
    def captcha_rec(img: BytesIO) -> str:
        return ocr(img).rec()

    def login(self):
        posturl = 'https://curricula.bfsu.edu.cn/academic/j_acegi_security_check'
        captchaurl = 'https://curricula.bfsu.edu.cn/academic/getCaptcha.do'
        n = 0
        while n < 10:
            n += 1
            capimg = self.session.get(captchaurl).content
            captcha = self.captcha_rec(BytesIO(capimg))
            postdata = {'groupId': '', 'j_username': self.stuid, 'j_password': self.password, 'j_captcha': captcha,
                        'button1': '登陆'}
            response = self.session.post(posturl, data=postdata)
            if response.text.find('验证码') == -1:
                self.login_time = time.time()
                return
        raise TimeoutError

    def get_score(self, datestr):
        posturl = 'https://curricula.bfsu.edu.cn/academic/manager/score/studentOwnScore.do?groupId=&moduleId=2020'
        yearid, termid = str2term(datestr)
        postdata = {'year': yearid, 'term': termid, 'para': '0', 'sortColumn': '', 'Submit': '查询'}
        content = self.session.post(posturl, data=postdata).text
        data = BeautifulSoup(content, 'html.parser').find('table', {'class': 'datalist'})
        if not data:
            return
        result = []
        magicflag = False  # Magic method, because the first tab is the headline and has no 'tr' and should be skipped.
        for tab in data.find_all('tr'):
            if not magicflag:
                magicflag = True
                continue
            course = []
            for tdd in tab.find_all('td'):
                course.append(tdd.string.strip())
            result.append(course)
        return result

    def get_userid(self):
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                  'Referer': 'https://curricula.bfsu.edu.cn/academic/manager/electcourse/stusced.do'}
        self.session.headers = header
        url = r'https://curricula.bfsu.edu.cn/academic/manager/electcourse/stusced.do#fastsc'
        response = self.session.get(url).text
        if response.find('ServletException') >= 0:
            raise UseridError
        result = BeautifulSoup(response, 'html.parser').find('input', attrs={'type': 'hidden', 'name': 'checkUserid'})
        if not result:
            return
        return result['value']

    def quickselect(self, courseid, seq='1'):
        """ flag 1: select successfully; 2: select unsuccessfully; 3: drop successfully; 4:drop unsuccessfully"""
        n = 0
        while n < 5:
            userid = self.get_userid()
            if not userid:
                n += 1
            else:
                break
        else:
            raise UseridError
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                  'Referer': 'https://curricula.bfsu.edu.cn/academic/manager/electcourse/stusced.do'}
        url = 'https://curricula.bfsu.edu.cn/academic/manager/electcourse/scaddaction.do'
        self.session.headers = header
        postdata = {'pcourseid': courseid, 'seq': seq, 'checkUserid': userid, 'Submit': '选课'}
        response = self.session.post(url, data=postdata)
        result = BeautifulSoup(response, 'html.parser').center.body.find('script').string.strip().split('\n', 7)
        # message = result[4].split(r'"')[1]
        flag = int(result[5].split('=')[1][0])
        return flag

    def get_name(self):
        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:14.0) Gecko/20100101 Firefox/14.0.1',
                  'Referer': 'https: // curricula.bfsu.edu.cn / academic / index_new.jsp'}
        url = 'https://curricula.bfsu.edu.cn/academic/showHeader.do'
        self.session.headers = header
        response = self.session.get(url).text
        self.tt = response
        result = re.search(r'<span>(.{0,10})\(\d{8}\)</span>', response)
        if result is not None:
            try:
                name = result.group(1)
            except IndexError:
                return
            else:
                return name
        return
