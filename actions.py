#! /usr/bin/python3
# coding=utf-8
import sqlite3
import threading
import time
import os
import re
import itchat

from bfsujwc import Query, UseridError
from utils import strftimestamp, form2pic


class Login(threading.Thread):
    def __init__(self, login_queue, special_status, status_lock, query_pool, query_lock):
        super(Login, self).__init__()
        self.login_queue = login_queue
        self.status = {}  # key: wechatid, value: [status_num, stuid, password]
        self.connection = sqlite3.connect('./data/jwc.db', check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.special_status = special_status
        self.status_lock = status_lock
        self.query_pool = query_pool
        self.query_lock = query_lock

    def exit(self, wechatid):
        self.status.pop(wechatid)
        self.status_lock.acquire()
        self.special_status.pop(wechatid)
        self.status_lock.release()

    def run(self):
        """ status:
                    1. waiting for student id (removed for better multithreading support);
                    2. waiting for password;
                    3. waiting for confirm;
                    0. waiting for overwrite confirm"""
        while 1:
            wechatid, text = self.login_queue.get()  # get a tuple( wechatid, text)
            status = self.status.get(wechatid)
            if not status:
                try:
                    int(text)
                except ValueError:
                    itchat.send_msg('学号应为8位纯数字，请重新输入纯数字学号', wechatid)
                except AssertionError:
                    itchat.send_msg('学号应为8位纯数字，请重新输入8位学号', wechatid)
                else:
                    cursor = self.connection.execute('SELECT * FROM User WHERE wechatid == ?', (wechatid,))
                    dbresult = cursor.fetchone()
                    cursor.close()
                    if not dbresult:
                        login_flag = 0
                    else:
                        # noinspection PyTypeChecker
                        if dbresult['id'] == text:
                            login_flag = 1
                        else:
                            login_flag = -1
                    if login_flag == 0:  # wechatid never login
                        self.status[wechatid] = [2, text]
                        itchat.send_msg('请回复教务网站密码', wechatid)
                    elif login_flag == 1:  # already login
                        self.exit(wechatid)
                        itchat.send_msg('你已经完成过此学号的登录，无需重复登录\n已退出登陆流程', wechatid)
                    else:  # id ever login but not this studentid
                        self.status[wechatid] = [0, text]
                        # noinspection PyTypeChecker
                        itchat.send_msg('本微信账号已于{}与学号{}绑定，重新绑定请回复 overwrite ，否则请回复 1 退出'.format(
                            strftimestamp(dbresult['createtime']), dbresult['id']), wechatid)
            elif status[0] == 2:
                self.status[wechatid][0] = 3
                self.status[wechatid].append(text)
                itchat.send_msg('正在验证请稍候……', wechatid)
                query = Query(self.status[wechatid][1], self.status[wechatid][2])
                try:
                    query.login()
                except TimeoutError:
                    self.exit(wechatid)
                    itchat.send_msg('验证失败，请确认学号密码后回复 login 重新尝试', wechatid)
                    del query
                else:
                    name = query.get_name()
                    cursor = self.connection.cursor()
                    cursor.execute('SELECT id FROM ID WHERE id == ?', (status[1],))
                    checkresult = cursor.fetchone()
                    if name is not None:
                        if not checkresult:
                            cursor.execute('INSERT INTO ID VALUES (?, ?, ?, 0)', (status[1], text, name))
                        cursor.execute('INSERT INTO User VALUES (?, ?, ?, ?)',
                                       (wechatid, status[1], query.login_time, query.login_time))
                    else:
                        if not checkresult:
                            cursor.execute('INSERT INTO ID VALUES (?, ?, NULL, 0)', (status[1], text))
                        cursor.execute('INSERT INTO User VALUES (?, ?, ?, ?)',
                                       (wechatid, status[1], query.login_time, query.login_time))
                    self.connection.commit()
                    cursor.close()
                    self.exit(wechatid)
                    itchat.send_msg('验证成功，回复 选课 尝试选课，回复 查分 查询成绩，更多帮助请回复 h ', wechatid)
                    self.query_lock.acquire()
                    self.query_pool[status[1]] = query
                    self.query_lock.release()
            elif status[0] == 0:
                if text == 'overwrite':
                    self.status[wechatid][0] = 2
                    itchat.send_msg('请回复该学号的教务网站密码', wechatid)
                elif text == '1':
                    self.exit(wechatid)
                    itchat.send_msg('已退出登录程序', wechatid)
                else:
                    itchat.send_msg('重新绑定请回复 overwrite ，否则请回复 1 退出', wechatid)


class GetScore(threading.Thread):
    def __init__(self, get_score_queue, query_pool, query_pool_lock, special_status, status_lock):
        super(GetScore, self).__init__()
        self.queue = get_score_queue
        self.pool = query_pool
        self.p_lock = query_pool_lock
        self.special_status = special_status
        self.status_lock = status_lock
        self.conn = sqlite3.connect('./data/jwc.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def exit(self, wechatid):
        self.status_lock.acquire()
        self.special_status.pop(wechatid)
        self.status_lock.release()

    def get_query(self, stuid, password):
        self.p_lock.acquire()
        query = self.pool.get(stuid)
        self.p_lock.release()
        if not query or query.login_time < time.time() - 1800:
            query = Query(stuid, password)
            query.login()
            self.p_lock.acquire()
            self.pool[stuid] = query
            self.p_lock.release()
            return query
        else:
            return query

    @classmethod
    def send_score_img(cls, score, wechatid):
        path = form2pic(score, './scoreimgtemp/' + str(time.time() * 1000) + '.bmp')
        itchat.send_image(path, wechatid)
        time.sleep(10)
        os.remove(path)

    def run(self):
        while 1:
            wechatid, text = self.queue.get()
            cursor = self.conn.execute(
                'SELECT User.id, ID.password FROM User, ID WHERE User.id == ID.id AND User.wechatid == ?', (wechatid,))
            dbresult = cursor.fetchone()
            cursor.close()
            if not dbresult:
                self.exit(wechatid)
                itchat.send_msg('本微信号尚未绑定任何账号，请回复 login 进行绑定后重试', wechatid)
            else:
                query = self.get_query(dbresult['id'], dbresult['password'])
                result = query.get_score(text)
                if not result:
                    self.exit(wechatid)
                    itchat.send_msg('翻了翻似乎你这学期并没有成绩……将退出查分', wechatid)
                else:
                    itchat.send_msg('正在生成{}年{}季学期成绩，请稍候……'.format(result[0][0], result[0][1]), wechatid)
                    thread = threading.Thread(target=GetScore.send_score_img, args=(result, wechatid))
                    thread.setDaemon(True)
                    thread.start()
                    self.exit(wechatid)


class SelectCourse(threading.Thread):
    pattern = re.compile(r'(.+);(\d+)')

    def __init__(self, queue, query_pool, query_pool_lock, special_status, special_status_lock):
        super().__init__()
        self.queue = queue
        self.pool = query_pool
        self.p_lock = query_pool_lock
        self.special_status = special_status
        self.status_lock = special_status_lock
        self.conn = sqlite3.connect('./data/jwc.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def exit(self, wechatid):
        self.status_lock.acquire()
        self.special_status.pop(wechatid)
        self.status_lock.release()

    def get_query(self, stuid, password):
        self.p_lock.acquire()
        query = self.pool.get(stuid)
        self.p_lock.release()
        if not query or query.login_time < time.time() - 1800:
            query = Query(stuid, password)
            query.login()
            self.p_lock.acquire()
            self.pool[stuid] = query
            self.p_lock.release()
            return query
        else:
            return query

    def run(self):
        while 1:
            wechatid, text = self.queue.get()
            if ';' in text:
                split = self.__class__.pattern.match(text)
                if not split:
                    itchat.send_msg('课序号应为纯数字，请检查输入后重新输入', wechatid)
                    continue
                else:
                    courseid = split.group(1)
                    courseseq = split.group(2)
            else:
                courseid = text
                courseseq = '1'
            cursor = self.conn.execute(
                'SELECT User.id, ID.password FROM User, ID WHERE User.id == ID.id AND User.wechatid == ?', (wechatid,))
            dbresult = cursor.fetchone()
            cursor.close()
            if not dbresult:
                self.exit(wechatid)
                itchat.send_msg('本微信号尚未绑定任何账号，请回复 login 进行绑定后重试', wechatid)
            else:
                query = self.get_query(dbresult['id'], dbresult['password'])

                def select(self, query, wechatid):
                    for _ in range(3):
                        try:
                            if query.quickselect(courseid, courseseq) == 1:
                                self.exit(wechatid)
                                itchat.send_msg('选课成功！请务必注意及时登陆教务系统检查！', wechatid)
                                break
                        except UseridError:
                            self.exit(wechatid)
                            itchat.send_msg('获取选课信息失败，请确认选课系统已开放\n已退出选课流程', wechatid)
                            break
                    else:
                        self.exit(wechatid)
                        itchat.send_msg('尝试失败，请确认无误后重新尝试或手动选课\n已退出选课流程', wechatid)

                t = threading.Thread(target=select, args=(self, query, wechatid))
                t.setDaemon(True)
                itchat.send_msg('正在尝试选课请稍后……', wechatid)
                t.start()


class QueryManager(threading.Thread):
    def __init__(self, query_pool, query_pool_lock):
        super(QueryManager, self).__init__()
        self.pool = query_pool
        self.lock = query_pool_lock

    def run(self):
        while 1:
            threshold_time = time.time()
            time.sleep(1800)
            self.lock.acquire()
            try:
                while self.pool.popitem(True)[1].login_time < threshold_time:
                    continue
            except KeyError:
                pass
            finally:
                self.lock.release()
