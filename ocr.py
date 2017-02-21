# coding: utf-8
# Copyright (c) 2009 - 2015, Aven's Lab. All rights reserved.
#                     http://www.ocrking.com
# DO NOT ALTER OR REMOVE COPYRIGHT NOTICES OR THIS FILE HEADER.
# Id: OcrKing.py,v 0.1 2014/10/29 23:40:18 
# The Python script for OcrKing Api
# By Aven <Aven@OcrKing.Com>
# Welcome to follow us 
# http://weibo.com/OcrKing
# http://t.qq.com/OcrKing
# Warning! 
# Before running this script , you should modify some parameter
# within the post data according to what you wanna do
# To run it manually,just type  python OcrKing.py
# the result will be shown soon
# Just Enjoy The Fun Of OcrKing !
####
class ocr():
    def __init__(self, imgbytes):
        # version for Python OcrKing Client #
        self.__version__ = '0.1'
        # version for Python OcrKing Client #

        # OcrKing Api Url #
        self.__api_url__ = 'http://lab.ocrking.com/ok.html'
        # OcrKing Api Url #

        # libs need to import ###

        # libs need to import ###

        # just fix some known bug of Python , ignore this please ###
        # httplib.HTTPConnection._http_vsn = 10
        # httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'
        # just fix some known bug of Python , ignore this please ###
        # replace the word KEY below with your apiKey obtained by Email #
        self.key = b"51703569bc83ba3a76qKDwSqIlK5zxFHE1ilHfhOPxhM2qpoYGLYWEQYYxBo578t2aylwHc7g"
        self.img = imgbytes

    ### post data with file uploading ###
    def post_multipart(self, fields, files):
        content_type, body = self.encode_multipart(fields, files)
        headers = {'Content-Type': content_type,
                   'Content-Length': str(len(body)),
                   'Accept-Encoding': 'gzip, deflate',
                   'Referer': 'http://lab.ocrking.com/?pyclient' + self.__version__,
                   'Accept': '*/*'}
        r = urllib.request.Request(self.__api_url__, body, headers)
        return urllib.request.urlopen(r).read()

    ### format the data into multipart/form-data ###
    def encode_multipart(self, fields, files):
        LIMIT = b'----------OcrKing_Client_Aven_s_Lab_L$'
        CRLF = b'\r\n'
        L = []
        for (key, value) in fields:
            L.append(b'--' + LIMIT)
            L.append(b'Content-Disposition: form-data; name="%s"' % key)
            L.append(b'')
            L.append(value)
        for (key, filename, value) in files:
            L.append(b'--' + LIMIT)
            L.append(b'Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append(b'Content-Type: application/octet-stream')
            L.append(b'')
            L.append(value)
        L.append(b'--' + LIMIT + b'--')
        L.append(b'')
        body = CRLF.join(L)
        content_type = b'multipart/form-data; boundary=%s' % LIMIT
        return content_type, body

    def rec(self):
        # you need to specify the full path of image you wanna OCR #
        # e.x. D:\\Program Files\\004.png #
        image = self.img
        # you need to modify the filename according to you real filename #
        # e.x 004.png #
        file = [(b'ocrfile', b'0.jpg', image.read())]
        fields = [(b'url', b''), (b'service', b'OcrKingForCaptcha'), (b'language', b'eng'), (b'charset', b'1'),
                  (b'apiKey', self.key),
                  (b'type', b'https://curricula.bfsu.edu.cn/academic/getCaptcha.do?0.5241544468256751')]
        # just fire the post action #
        xml = self.post_multipart(fields, file)
        parser = etree.XMLParser(recover=True)
        tree = etree.fromstring(xml, parser=parser)
        result = tree.find('ResultList').find('Item').find('Result').text
        # print the result #
        return result


import urllib
from io import BytesIO

from lxml import etree

if __name__ == "__main__":
    #    from io import BytesIO
    with open("0.bmp", 'rb') as f:
        img = BytesIO(f.read())
        print(ocr(img).rec())
    input()
