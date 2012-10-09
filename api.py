# -*- coding: utf-8 -*-

# utils.py by:
#    Agustin Zubiaga <aguz@sugarlabs.org>
#    Cristhofer Travieso <cristhofert97@gmail.com>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import os
import subprocess
import tempfile
import magic

sys.path.insert(0, 'lib')

import paramiko
import json

OPEN_COMMAND = 'xdg-open %s' if 'linux' in sys.platform else '%s'

SERVER = '192.168.1.100'
USERNAME = 'profesores'
RSAKEY = os.path.join(os.getenv('HOME'), '.ssh', 'id_rsa')
GROUPS_DIR = '/home/servidor/Groups'
HOMEWORKS_DIR = '.homeworks'


def _get_config():
    '''Devuelve el contenido del archivo config'''
    _file = open('config')
    data = json.load(_file)
    _file.close()

    return data

SUBJECT, NAME = _get_config()


def generate_rsa_key():
    '''Genera la clave ssh'''
    stdout_file = tempfile.mktemp()
    p = subprocess.Popen('ssh-keygen',
                          shell=True,
                          stdin=subprocess.PIPE,
                          stdout=open(stdout_file, 'w+b'),
                          stderr=open(stdout_file, 'r+b'),
                          universal_newlines=False)
    for i in range(3):
        p.stdin.write('')
        p.stdin.flush()


def connect_to_server():
    """Connects to sftp server"""
    transport = paramiko.Transport((SERVER, 22))
    rsakey = paramiko.RSAKey.from_private_key_file(RSAKEY, password='')
    transport.connect(username=USERNAME, pkey=rsakey)

    sftp = paramiko.SFTPClient.from_transport(transport)

    return sftp


def save_document(sftp, uri, group, title, description):
    """Saves a document in the server"""
    sftp.chdir(os.path.join(GROUPS_DIR, group, SUBJECT))
    local_file = open(uri)
    remote_file = sftp.open(title, 'w')
    remote_file.write(local_file.read())
    local_file.close()
    remote_file.close()

    desc = sftp.open('.desc', 'r')
    info = json.load(desc)
    desc.close()
    mime_type = magic.from_file(uri, mime=True)

    #FIXME: Save the mime type
    info[title] = (description, NAME, mime_type)

    desc = sftp.open('.desc', 'w')
    json.dump(info, desc)
    desc.close()


def get_homeworks(sftp, group):
    '''Devuelve la lista de las tareeas domiciliarias'''
    sftp.chdir(os.path.join(GROUPS_DIR, group, SUBJECT, HOMEWORKS_DIR))
    _desc = sftp.open('.desc', 'r')
    desc = json.load(_desc)
    _desc.close()
    homeworks = {}
    for hw in sftp.listdir('.'):
        if not hw.startswith('.'):
            homeworks[hw] = desc[hw]
    return homeworks


def get_homework(sftp, group, hw, extension, uri=None, _open=True):
    '''Devuelve una tarea domiciliaria'''
    sftp.chdir(os.path.join(GROUPS_DIR, group, SUBJECT, HOMEWORKS_DIR))

    if not uri:
        file_path = tempfile.mktemp()
    else:
        file_path = uri
    if not extension in file_path:
        file_path += extension
    sftp.get(hw, file_path)

    if _open:
        subprocess.Popen(OPEN_COMMAND % file_path, shell=True)

    return file_path


def evaluate_homework(sftp, group, hw, evaluation):
    '''Se  utilisa para evluar una tarea domiciliaria'''
    sftp.chdir(os.path.join(GROUPS_DIR, group, SUBJECT, HOMEWORKS_DIR))
    _desc = sftp.open('.desc', 'r')
    desc = json.load(_desc)
    _desc.close()
    date, comments, s_evaluation, student, mimetype, extension = desc[hw]
    desc[hw] = (date, comments, evaluation, student, mimetype, extension)

    _desc = sftp.open('.desc', 'w')
    json.dump(desc, _desc)
    _desc.close()
