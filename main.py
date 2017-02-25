#! /usr/bin/python3
# coding=utf-8
import queue
import threading

import itchat

from actions import QueryManager, Login, GetScore, SelectCourse
from utils import autoreply, showqrcode, LastUpdatedOrderedDict

login_queue = queue.Queue(maxsize=30)
get_score_queue = queue.Queue(maxsize=30)
select_course_queue = queue.Queue(maxsize=30)


@itchat.msg_register('Friends')
def add_friends(msg):
    welcomemsg = '''你好~\n
    一个并不成熟的工具，希望能帮助到(北外的)你\n
    首次使用查询成绩、快速选课等功能前，请回复login进行登录\n
    回复 h 获得进一步帮助\n
    源码请访问项目主页：还没建好\n'''
    itchat.add_friend(**msg['Text'])
    # occupied for check wechatid
    itchat.send_msg(welcomemsg, msg['RecommendInfo']['UserName'])


command_words = {'login': 'login', '选课': 'select_course', '查分': 'get_score'}
special_status = {}  # {wechatid: 'login'| 'get_score'| 'select_course'...}
status_lock = threading.RLock()
status_queue = {'login': login_queue, 'get_score': get_score_queue, 'select_course': select_course_queue}
welcome_msgs = {'login': '请回复你的学号',
                'get_score': '请回复要查询的学期，\n如2016年秋季学期请回复\n2016a\ns(spring)=春；a(autumn)=秋\n回复其他任意信息将默认查询上一学期的成绩',
                'select_course': '***须知\n  工具未经大量测试谨慎使用\n    请输入课程的课程号(及课序号，一般为1，不填默认为1)，你可以从通知文件中获取、从其他已登入系统的同学处窥得……\n输入格式为\n 课程号[;课序号]\n    方括号内为选填内容，若选填课序号请将二者用分号隔开\n    *根据教务处通知，本学期校通选课为区分2014级/2015 16级，出现多门通选不同模块相同课程相同课程号相同课序号，由此导致的后果未知；因此选课成功后请务必人工登录教务系统确认，后果自负'}

query_pool = LastUpdatedOrderedDict()  # {'stuid': Query}
query_pool_lock = threading.RLock()


@itchat.msg_register('Text', isGroupChat=False)
def text_reply(msg):
    global special_status, status_lock
    status_lock.acquire()
    user_status = special_status.get(msg['FromUserName'])
    status_lock.release()
    if user_status:
        status_queue[user_status].put((msg['FromUserName'], msg['Text']))
        return
    elif msg['Text'] in command_words:
        user_status = command_words[msg['Text']]
        status_lock.acquire()
        special_status[msg['FromUserName']] = user_status
        status_lock.release()
        return welcome_msgs[user_status]
    elif msg['Text'] == 'h':
        helpmsg = \
            '''             ******帮助******
          目前提供成绩查询、快速选课功能，仅支持北京外国语大学教务系统。
          在首次使用教务相关功能前请回复 login 进行登录
          请注意，当前选课前必须知道目标课程的课程编号！
              成绩查询 请回复 查分
              快速选课 请回复 选课
          除此以外的消息你将会和一个智力低下的机器人聊天，据说她能查天气询时事之类……诸位自行探索
          开发细节和碎碎念请回复 -help 获取
                           2017/1/30'''
        return helpmsg
    else:
        return autoreply(msg['Text'], msg['FromUserName'])  # needed to be optimized


daemon_thread_list = [QueryManager(query_pool, query_pool_lock),
                      Login(login_queue, special_status, status_lock, query_pool, query_pool_lock),
                      GetScore(get_score_queue, query_pool, query_pool_lock, special_status, status_lock),
                      SelectCourse(select_course_queue, query_pool, query_pool_lock, special_status, status_lock)]
# itchat.auto_login(qrCallback=showqrcode, hotReload=True) # test on PC
itchat.auto_login(enableCmdQR=2, hotReload=True)  # run on server
for thread in daemon_thread_list:
    thread.setDaemon(True)
    thread.start()
itchat.run()
