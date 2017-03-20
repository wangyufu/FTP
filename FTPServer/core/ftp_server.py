#!/usr/bin/env python
import configparser
import hashlib
import json
import os
import sys
import socketserver

import subprocess

import struct

import re
from conf import settings

STATUS_CODE = {
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd ",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",
    255: "Filename doesn't provided",
    256: "File doesn't exist on server",
    257: "ready to send file",
    258: "md5 verification",
    259: "ready to recv file",
    260: "There is insufficient space on the hard disk",
    261: "successfully delete",
    262: "Delete failed",
    263: "without this path",
    264: "switching path to success",
}


class FTPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            self.data = self.request.recv(1024).strip()
            print(self.client_address[0])
            print(self.data)
            if not self.data:
                print('chient closed...')
                break
            data = json.loads(self.data.decode())
            if data.get('action') is not None:
                if hasattr(self, '_%s' % data.get('action')):
                    func = getattr(self, '_%s' % data.get('action'))
                    func(data)
                else:
                    print('invalid cmd')
                    self.send_response(251)
            else:
                print('invalid cmd format')
                self.send_response(250)

    def send_response(self, status_code, data=None):
        response = {'status_code': status_code, 'status_msg': STATUS_CODE[status_code]}
        if data:
            response.update(data)
        self.request.send(json.dumps(response).encode())

    def _getdirsize(self, dir):
        size = 0
        for root, dirs, files in os.walk(dir):
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return size

    def _auth(self, *args, **kwargs):
        data = args[0]
        if data.get('username') is None or data.get('password') is None:
            self.send_response(252)

        user = self.authenticate(data.get('username'), data.get('password'))
        if user is None:
            self.send_response(253)
        else:
            print('passed authentication', user)
            self.user = user
            self.send_response(254)
        self.user_home_dir = '%s\%s' % (settings.USER_HOME, self.user)

    def _get(self, *args, **kwargs):
        data = args[0]
        if data.get('filename') is None:
            self.send_response(255)
        user_home_dir = '%s/%s' % (settings.USER_HOME, self.user)
        file_abs_path = '%s/%s' % (user_home_dir, data.get('filename'))

        if os.path.isfile(file_abs_path):
            file_obj = open(file_abs_path, 'rb')
            file_size = os.path.getsize(file_abs_path)
            self.send_response(257, data={'file_size': file_size})
            self.request.recv(1)
            if data.get('md5'):
                md5_obj = hashlib.md5()
                for line in file_obj:
                    self.request.send(line)
                    md5_obj.update(line)
                else:
                    file_obj.close()
                    md5_val = md5_obj.hexdigest()
                    self.send_response(258, data={'md5': md5_val})
                    print('send file done')
            else:
                for line in file_obj:
                    self.request.send(line)
                else:
                    file_obj.close()
                    print("send file done....")

    def _put(self, *args, **kwargs):
        data = args[0]
        if data.get('filename') is None:
            self.send_response(255)
        file_abs_path = '%s\%s' % (self.user_home_dir, data.get('filename').split('\\')[-1])
        file_size = self._getdirsize('%s\%s' % (settings.USER_HOME, self.user))
        # print(type(file_size),type(os.path.join(file_abs_path)),type(self.disk_quota))
        if file_size + os.path.getsize(data.get('filename')) > int(self.disk_quota):
            self.send_response(260)
            return
        if os.path.isfile(data.get('filename')):
            file_obj = open(data.get('filename'), 'rb')
            self.send_response(259, data={'file_abs_path': file_abs_path})
            md5_obj = hashlib.md5()
            if data.get('md5'):
                for line in file_obj:
                    self.request.send(line)
                    md5_obj.update(line)
                else:
                    file_obj.close()
                    md5_val = md5_obj.hexdigest()
                    self.send_response(258, data={'md5': md5_val})
                    print("put file done....")

            else:
                for line in file_obj:
                    self.request.send(line)
                else:
                    file_obj.close()
                    print("put file done....")

    def _ls(self, *args, **kwargs):
        print(self.user_home_dir)
        res = subprocess.Popen('dir ' + self.user_home_dir,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        err = res.stderr.read()
        if err:
            back_msg = err
        else:
            back_msg = res.stdout.read()
        head_dic = {
            'data_size': len(back_msg)
        }
        head_json = json.dumps(head_dic)
        head_bytes = head_json.encode('utf-8')
        self.request.send(struct.pack('i', len(head_bytes)))
        self.request.send(head_bytes)
        # 第四阶段：发真实数据
        self.request.sendall(back_msg)

    def _cd(self, *args, **kwargs):
        data = args[0]
        cd_dir = os.path.join(self.user_home_dir, data.get('path'))
        home_dir = '%s\%s' % (settings.USER_HOME, self.user)
        # print(os.path.abspath(cd_dir).startswith(home_dir))
        if os.path.isdir(cd_dir) and os.path.abspath(cd_dir).startswith(home_dir):
            self.user_home_dir = cd_dir
            self.send_response(264)
        else:
            self.send_response(263)

    def _pwd(self, *args, **kwargs):
        pwd = self.user_home_dir.replace(settings.USER_HOME, '')
        self.request.send(json.dumps(pwd).encode())

    def _del(self, *args, **kwargs):
        data = args[0]
        del_file = os.path.join(self.user_home_dir, data['file'])
        if os.path.isfile(del_file):
            os.remove(del_file)
            self.send_response(261)
        else:
            self.send_response(262)

    def authenticate(self, username, password):
        config = configparser.ConfigParser()
        config.read(settings.ACCOUNT_FILE)
        if username in config.sections():
            _password = config[username]['Password']
            if _password == password:
                print('pass auth [%s]' % username)
                self.disk_quota = config[username]['disk_quota']
                return username


