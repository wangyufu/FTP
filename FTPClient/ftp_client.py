#!/usr/bin/env python
import hashlib
import json
import os
import optparse
from socket import *

import struct


class FTPClient(object):
    def __init__(self):
        parser = optparse.OptionParser()
        parser.add_option('-s', '--server', dest='server', help='ftp server ip_addr')
        parser.add_option("-P", "--port", type="int", dest="port", help="ftp server port")
        parser.add_option("-u", "--username", dest="username", help="username")
        parser.add_option("-p", "--password", dest="password", help="password")
        self.options, self.args = parser.parse_args()
        self.verify_args(self.options, self.args)
        self.make_connection()

    def verify_args(self, options, args):
        '''校验参数合法型'''
        if options.server and options.port:
            if 0 < options.port < 65535:
                return True
            else:
                exit('Err:host port must in 0-65535')

    def make_connection(self):
        self.sock = socket()
        print(self.options.server, self.options.port)
        self.sock.connect((self.options.server, self.options.port))

    def interactive(self):
        if self.authenticate():
            print('start interactive'.center(30, '-'))
            while True:
                choice = input('[%s]:' % self.username).strip()
                if len(choice) == 0:
                    continue
                if choice == 'exit':
                    break
                cmd_list = choice.split()
                if hasattr(self, '_%s' % cmd_list[0]):
                    func = getattr(self, '_%s' % cmd_list[0])
                    func(cmd_list)
                else:
                    print('Invalid cmd.')
            self.sock.close()

    def authenticate(self):
        if self.options.username:
            return self.get_auth_result(self.options.username, self.options.password)
        else:
            retry_count = 0
            while retry_count < 3:
                username = input('username:').strip()
                password = input('password:').strip()
                return self.get_auth_result(username, password)

    def get_auth_result(self, username, password):
        data = {
            'action': 'auth',
            'username': username,
            'password': password
        }
        self.sock.send(json.dumps(data).encode(encoding='utf-8'))
        response = self.get_response()
        if response.get('status_code') == 254:
            print('Passed authentication')
            self.username = username
            return True
        else:
            print(response.get("status_msg"))

    def get_response(self):
        data = self.sock.recv(1024)
        data = json.loads(data.decode())
        return data

    def _help(self, cmd_list):
        msg = '''
            get：
            get <home dir file>
            get <home dir file>  --md5

            put：
            put <abs file>
            put <abs file>  --md5

            View the current file information：
            ls

            View the current path：
            pwd

            Switch directory：
            cd <Relative path>

            delete file：
            del <Relative path file>

            Out of the client：
            exit
        '''
        print(msg)

    def _put(self, cmd_list):
        print('get--', cmd_list)
        if len(cmd_list) == 1:
            print('no filename')
            return
        data_header = {
            'action': 'put',
            'filename': cmd_list[1],
        }
        if self.__md5_required(cmd_list):
            data_header['md5'] = True
        self.sock.send(json.dumps(data_header).encode(encoding='utf-8'))
        response = self.get_response()
        if response['status_code'] == 259:
            file_obj = open(response['file_abs_path'], 'wb')
            received_size = 0
            put_file = os.path.getsize(cmd_list[1])
            progress = self.show_progress(put_file)
            progress.__next__()
            if self.__md5_required(cmd_list):

                md5_obj = hashlib.md5()
                while received_size < put_file:
                    file_data = self.sock.recv(4096)
                    received_size += len(file_data)
                    try:
                        progress.send(len(file_data))
                    except StopIteration as e:
                        print('100%')
                    file_obj.write(file_data)
                    md5_obj.update(file_data)
                else:
                    file_obj.close()
                    print("put file done....")
                    md5_val = md5_obj.hexdigest()
                    md5_form_server = self.get_response()
                    if md5_form_server['status_code'] == 258:
                        if md5_form_server['md5'] == md5_val:
                            print('%s md5一致' % data_header['filename'].split('\\')[-1])

            else:
                while received_size < put_file:
                    file_data = self.sock.recv(4096)
                    received_size += len(file_data)
                    try:
                        progress.send(len(file_data))
                    except StopIteration as e:
                        print('100%')
                    file_obj.write(file_data)
                else:
                    print('recv file done....')
                    file_obj.close()
        else:
            print(response['status_msg'])

    def _get(self, cmd_list):
        print('get--', cmd_list)
        if len(cmd_list) == 1:
            print('no filename')
            return
        data_header = {
            'action': 'get',
            'filename': cmd_list[1]
        }
        if self.__md5_required(cmd_list):
            data_header['md5'] = True

        self.sock.send(json.dumps(data_header).encode(encoding='utf-8'))
        response = self.get_response()

        if response['status_code'] == 257:
            self.sock.send(b'1')
            base_filename = cmd_list[1].split('/')[-1]
            received_size = 0
            file_obj = open(base_filename, 'wb')
            progress = self.show_progress(response['file_size'])
            progress.__next__()
            if self.__md5_required(cmd_list):
                md5_obj = hashlib.md5()
                while received_size < response['file_size']:
                    data = self.sock.recv(4096)
                    received_size += len(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                    file_obj.write(data)
                    md5_obj.update(data)
                else:
                    print('file recv done')
                    file_obj.close()
                    md5_val = md5_obj.hexdigest()
                    md5_form_server = self.get_response()
                    if md5_form_server['status_code'] == 258:
                        if md5_form_server['md5'] == md5_val:
                            print('%s md5一致' % base_filename)

            else:
                while received_size < response['file_size']:
                    data = self.sock.recv(4096)
                    received_size += len(data)
                    try:
                        progress.send(len(data))
                    except StopIteration as e:
                        print('100%')
                    file_obj.write(data)
                else:
                    print('file rece done')
                    file_obj.close()

    def _ls(self, cmd_list):
        data_header = {
            'action': 'ls',
        }
        self.sock.send(json.dumps(data_header).encode(encoding='utf-8'))

        head = self.sock.recv(4)
        head_size = struct.unpack('i', head)[0]
        print(head_size)

        # 收报头（根据报头长度）
        head_bytes = self.sock.recv(head_size)
        head_json = head_bytes.decode('utf-8')
        head_dic = json.loads(head_json)
        '''
          head_dic={
                    'data_size':len(back_msg)
                }
        '''
        data_size = head_dic['data_size']  # 取出真实数据的长度

        # 收真实的数据
        recv_size = 0
        recv_bytes = b''
        while recv_size < data_size:
            res = self.sock.recv(1024)
            recv_bytes += res
            recv_size += len(res)
        print(recv_bytes.decode('gbk'))

    def _pwd(self, cmd_list):
        data_header = {
            'action': 'pwd',
        }
        self.sock.send(json.dumps(data_header).encode(encoding='utf-8'))
        pwd = self.sock.recv(1024)
        print(pwd.decode('utf-8'))

    def _cd(self, cmd_list):
        if len(cmd_list) == 1:
            print('no path')
            return
        data_header = {
            'action': 'cd',
            'path': cmd_list[1]
        }
        self.sock.send(json.dumps(data_header).encode(encoding='utf-8'))
        response = self.get_response()
        if response['status_code'] == 264:
            print(response['status_msg'])
        else:
            print(response['status_msg'])

    def _del(self, cmd_list):
        if len(cmd_list) == 1:
            print('no path')
            return
        data_header = {
            'action': 'del',
            'file': cmd_list[1]
        }
        self.sock.send(json.dumps(data_header).encode(encoding='utf-8'))
        response = self.get_response()
        if response['status_code'] == '261':
            print(response['status_msg'])
        else:
            print(response['status_msg'])

    def __md5_required(self, cmd_list):
        if '--md5' in cmd_list:
            return True

    def show_progress(self, total):
        received_size = 0
        current_percent = 0
        while received_size < total:
            if int((received_size / total) * 100) > current_percent:
                print('#', end='', flush=True)
                current_percent = int((received_size / total) * 100)
            new_size = yield
            received_size += new_size


if __name__ == '__main__':
    ftp = FTPClient()
    ftp.interactive()
