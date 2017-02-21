#! /usr/bin/python3
# coding=utf-8

import collections
import json
import os
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont


def autoreply(question, userid):
    tulingpostdata = {"key": "c4b7a224434e4d1a850b01f3712cbd5f", "info": question, "userid": userid}
    response = requests.post(r'http://www.tuling123.com/openapi/api', data=tulingpostdata)
    result = json.loads(response.text)
    if result['text'] == '当前请求调用次数已用尽':
        return '今天累了，睡了'
    elif not 0 <= int(result['code']) < 200000:
        return '我病了……能联系到他的话告诉他一声'
    else:
        return result['text']


def form2pic(form, fileobj):
    """ form is a list，whose elements are also lists，which contain strings
    output a BytesIO containing a bmp"""
    font = ImageFont.truetype("inziu-SC-regular.ttc", 12)  # origin 12
    # 特殊调整
    head = '|{:^2}|{:^2}|{:^11}|{:^31}|{:^3}|{:^8}|{:^7}|{:>2}|{:^4}|{:^4}|'.format('学年', '学期', '课程号', '课程名', '课序号',
                                                                                    '总评',
                                                                                    '学分', '学时', '考试性质', '及格标志')
    form.insert(0, ["-" * 92])
    form.insert(0, [head])
    form.insert(0, ["=" * 92])
    # end
    line_num = len(form)
    height = (line_num + 5) * (12 + 2)  # 12+行距
    length = 28 + font.getsize(head)[0]
    im = Image.new("RGB", (length, height), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    x, y = 14, 12
    for line in form:
        line = "".join(line)
        draw.text((x, y), line, font=font, fill="#000000")
        y += 14

    if isinstance(fileobj, (str, bytes)):
        im.save(os.path.join(os.path.dirname(__file__), 'static', str(fileobj) + '.bmp'))
        return 1
    else:
        im.save(fileobj, "bmp")
        return fileobj


def showqrcode(uuid, status, qrcode):
    im = Image.open(BytesIO(qrcode))
    im.show()


class LastUpdatedOrderedDict(collections.OrderedDict):
    'Store items in the order the keys were last added'

    def __setitem__(self, key, value, **kwargs):
        if key in self:
            del self[key]
        super(LastUpdatedOrderedDict, self).__setitem__(self, key, value)
