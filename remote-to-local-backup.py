"""Recursive full backup.

Usage:
  remote-to-local-backup bkp SERVER USER REMOTE_DIR LOCAL_DIR
  remote-to-local-backup (-h | --help)

Arguments:
  SERVER        Remote server from which to backup. It is assumed the passwordless authentication using public SSH key has already been set up
  USER        User id to login to remote server
  REMOTE_DIR  Full path of the remote directory to backup
  LOCAL_DIR   Full path of the local directory inside which the backup will be created. The name of the created local backup directory will be <remote_dir_name>-timestamp

Options:
  -h, --help     Show this screen.

"""

import sys
import os
from datetime import datetime
import paramiko
import stat
from docopt import docopt


def setup_dir(local_dir, remote_dir):
    remote_folder = os.path.basename(os.path.normpath(remote_dir))
    os.chdir(local_dir)
    now = datetime.now()
    date_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    backup_dir = remote_folder+'-'+date_time
    os.mkdir(backup_dir)
    os.chdir(backup_dir)
    return os.getcwd()

def setup_conn(server, user, password=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy)
    ssh.load_system_host_keys()
    ssh.connect(server, username=user, password=None)
    sftp = ssh.open_sftp()
    return sftp

def recursive_copy(src, dest, sftp, total, count=1):   
    if not os.path.isdir(dest):
        os.makedirs(dest)
    for item in sftp.listdir_attr(src):
        item_name = str(item.filename)
        count += 1
        if stat.S_ISDIR(item.st_mode):
            recursive_copy(src + "/" + item_name, dest + "/" + item_name, sftp, total, count)
        else:
            print("Copying {} of {}: {}".format(count, total, item_name))
            sftp.get(src + "/" + item_name, dest + "/" + item_name)         

def get_file_count(sftp, src, dir_count=1, file_count=0):
    for item in sftp.listdir_attr(src):
        item_name = str(item.filename)
        print(item.filename, dir_count, file_count)
        if stat.S_ISDIR(item.st_mode):
            return get_file_count(sftp, src + "/" + item_name, dir_count+1, file_count)
        else:
            file_count +=1
    return dir_count, file_count

if __name__ == '__main__':
    args = docopt(__doc__, version='0.1')
    sftp = setup_conn(args['SERVER'], args['USER'])
    dir_root = setup_dir(args['LOCAL_DIR'], args['REMOTE_DIR'])
    print('Calculating how many to copy.')
    dir_count, file_count = get_file_count(sftp,args['REMOTE_DIR'])
    print('Copying {} files and {} directories from {} to {}'.format(file_count, dir_count, args['REMOTE_DIR'], dir_root))
    recursive_copy(args['REMOTE_DIR'], dir_root, sftp, dir_count + file_count)
    sftp.close()
  