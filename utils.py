#! /usr/bin/python3
# coding=utf-8

import collections
import json
import time
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont
import re


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


def count_2len_characters(string):
    rule = re.compile(r'[^\x00-\xff]')
    result = rule.findall(string)
    return len(result)


def reallen(string):
    return len(string) + count_2len_characters(string)


def form2pic(form, path=None):
    """ form is a list，whose elements are also lists，which contain strings
    output a BytesIO containing a bmp"""
    max_length = [4, 4, 6, 6, 6, 4, 4, 4, 8, 8]
    for index in range(len(form[0])):
        for _row in form:
            if reallen(_row[index]) > max_length[index]:
                max_length[index] = reallen(_row[index])
    font = ImageFont.truetype("inziu-SC-regular.ttc", 12)  # origin 12
    new_head = ('学年', '学期', '课程号', '课程名', '课序号', '总评', '学分', '学时', '考试性质', '及格标志')
    form.insert(0, new_head)
    _form = []
    for _row in form:
        _form.append([x.center(max_length[y] - count_2len_characters(x)) for y, x in enumerate(_row)])
    _form.insert(1, ["-" * (sum(max_length) + 11)])
    _form.insert(0, ["=" * (sum(max_length) + 11)])
    # end
    line_num = len(_form)
    height = (line_num + 5) * (12 + 2)  # 12+行距
    length = 28 + font.getsize(_form[0][0])[0]
    im = Image.new("RGB", (length, height), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    x, y = 14, 12
    for lineno, line in enumerate(_form):
        if lineno != 0 and lineno != 2:
            line = '|' + "|".join(line) + '|'
        else:
            line = '|'.join(line)
        draw.text((x, y), line, font=font, fill="#000000")
        y += 14

    if not path:
        fileobj = BytesIO()
        im.save(fileobj, "bmp")
        return fileobj
    elif path == 'im':
        return im
    else:
        im.save(path)
        return path


def showqrcode(uuid, status, qrcode):
    im = Image.open(BytesIO(qrcode))
    im.show()


class LastUpdatedOrderedDict(collections.OrderedDict):
    """Store items in the order the keys were last added"""

    def __setitem__(self, key, value, **kwargs):
        if key in self:
            del self[key]
        super(LastUpdatedOrderedDict, self).__setitem__(key, value)


def strftimestamp(timestamp: float = None, pattern: str = '%Y-%m-%d %H:%M:%S') -> str:
    if not timestamp:
        timestamp = time.time()
    return time.strftime(pattern, time.localtime(timestamp))
