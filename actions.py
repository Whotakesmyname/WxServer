#! /usr/bin/python3
# coding=utf-8
import sqlite3
import threading
import time

import itchat

from bfsujwc import Query


class Login(threading.Thread):
    def __init__(self, login_queue, special_status, status_lock, query_pool, query_lock):
        super(Login, self).__init__()
        self.login_queue = login_queue
        self.status = {}  # key: wechatid, value: [status_num, stuid, password]
        self.connection = sqlite3.connect('./data/jwc.db', check_same_thread=False)
        self.special_status = special_status
        self.status_lock = status_lock
        self.query_pool = query_pool
        self.query_lock = query_lock

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
                    cursor = self.connection.execute('SELECT * FROM user WHERE id == ?', (int(text),))
                    dbresult = cursor.fetchone()
                    cursor.close()
                    # noinspection PyTypeChecker
                    if not dbresult:  # id never login
                        self.status[wechatid] = [2, text]
                        itchat.send_msg('请回复教务网站密码', wechatid)
                    elif wechatid in dbresult['wechatid'].split(';'):  # ever login
                        self.status[wechatid] = [0, text]
                        itchat.send_msg('你已经完成过登录，覆盖原信息请回复overwrite，退出登录请回复1', wechatid)
                    else:  # id ever login but not this wechatid
                        self.status[wechatid] = [2, text]
                        itchat.send_msg('请回复教务网站密码', wechatid)
            elif status[0] == 2:
                self.status[wechatid][0] = 3
                self.status[wechatid].append(text)
                itchat.send_msg('正在验证请稍候……')
                query = Query(self.status[wechatid][1], self.status[wechatid][2])
                try:
                    query.login()  # needed to be recycled
                except TimeoutError:
                    self.status.pop(wechatid)
                    self.status_lock.acquire()
                    self.special_status.pop(wechatid)
                    self.status_lock.release()
                    itchat.send_msg('验证失败，请确认学号密码后回复 login 重新尝试', wechatid)
                    del query
                else:
                    name = query.get_name()
                    if name is not None:
                        self.connection.execute('INSERT INTO user VALUES (?, ?, ?, ?, ?)',
                                                (int(status[1]), wechatid, name, text, time.time()))
                    else:
                        self.connection.execute('INSERT INTO user VALUES (?, ?, NULL, ?, ?)',
                                                (int(status[1]), wechatid, text, time.time()))
                    self.connection.commit()
                    self.status.pop(wechatid)
                    self.status_lock.acquire()
                    self.special_status.pop(wechatid)
                    self.status_lock.release()
                    itchat.send_msg('验证成功，回复 选课 尝试选课，回复 查分 查询成绩，更多帮助请回复 h ', wechatid)
                    self.query_lock.acquire()
                    self.query_pool[status[1]] = query
                    self.query_lock.release()
            elif status[0] == 0:
                if text == 'overwrite':
                    self.status[wechatid][0] = 2
                    itchat.send_msg('请回复新的教务网站密码', wechatid)
                elif text == '1':
                    self.status.pop(wechatid)
                    self.status_lock.acquire()
                    self.special_status.pop(wechatid)
                    self.status_lock.release()
                    itchat.send_msg('已退出登录程序', wechatid)
                else:
                    itchat.send_msg('你已经完成过登录，覆盖原信息请回复overwrite，退出登录请回复1', wechatid)


class Get_Score(threading.Thread):
    def __init__(self, get_score_queue, query_pool, query_pool_lock, special_status, status_lock):
        super(Get_Score, self).__init__()
        self.queue = get_score_queue
        self.pool = query_pool
        self.p_lock = query_pool_lock
        self.special_status = special_status
        self.status_lock = status_lock

    def run(self):
        while 1:
            wechatid, text = self.queue.get()


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
                while self.pool.popitem(True).login_time < threshold_time:
                    continue
            except KeyError:
                pass
            finally:
                self.lock.release()
