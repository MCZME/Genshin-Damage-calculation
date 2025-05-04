import json
import tarfile
import paramiko
import os

from DataRequest import MongoDB
from core.Config import Config
from core.dataHandler.BatchDataAnalyze import BatchDataAnalyze

class LogSFTP:
    def __init__(self):
        # 创建SSH连接
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()

    def connect(self):
        try:
            self.ssh.connect(Config.get('batch.host'), port=22, username=Config.get('batch.username'), password=Config.get('batch.password'))
            print("SSH连接成功！")
        except Exception as e:
            print(f"SSH连接失败: {e}")

    def send_file(self, local_path, remote_path):
        try:
            sftp = self.ssh.open_sftp()
            # 分离远程目录和文件名
            remote_dir = os.path.dirname(remote_path)
            self.ensure_remote_dir_exists(sftp, remote_dir)  # 确保目录存在

            # 上传文件
            sftp.put(local_path, remote_path)
            print("文件上传成功！")
        except Exception as e:
            print(f"操作失败: {e}")
        finally:
            sftp.close() if 'sftp' in locals() else None
            self.ssh.close()

    def ensure_remote_dir_exists(self, sftp, remote_dir):
        """确保远程目录存在，不存在则递归创建"""
        try:
            sftp.stat(remote_dir)  # 检查目录是否存在
        except FileNotFoundError:
            dirname, basename = os.path.split(remote_dir.rstrip('/'))
            if dirname:  # 递归创建父目录
                self.ensure_remote_dir_exists(sftp, dirname)
            sftp.mkdir(remote_dir)  # 创建当前目录

def create_tar_gz(source_dir, output_filename):
    """
    压缩目录为tar.gz格式
    :param source_dir: 需要压缩的目录
    :param output_filename: 输出的tar.gz文件名
    """
    if not output_filename.endswith(".tar.gz"):
        output_filename += ".tar.gz"
    
    with tarfile.open(output_filename, "w:gz") as tar:
        # 遍历目录下的所有文件和子目录
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # 在压缩包中保持相对路径
                arcname = os.path.relpath(file_path, start=source_dir)
                tar.add(file_path, arcname=arcname)
        print(f"压缩完成：{output_filename}")

def send_file_to_remote(uid):
    file_path = f'./data/sim/{uid}/'
    create_tar_gz(file_path+'log', f'./data/sim/{uid}/{uid}.tar.gz')

    a = BatchDataAnalyze(uid)
    a.analyze()
    a.send_to_MongoDB()

    db = MongoDB('genshin_damage_report','configs')
    with open(file_path+'/config.json','r') as f:
        data = json.load(f)
        db.insert_document(data)
        print('配置文件插入成功')
    
    db.change_collection('simulations')
    for i in range(Config.get('batch.batch_sim_num')):
        with open(file_path+'data/'+uid+'_'+str(i)+'.json','r') as f:
            data = json.load(f)
            db.insert_document({
                'uid': uid,
                'num': i,
                'frames': data,
                'log_file_path': '/home/damage_sim_log/'+uid+'.tar.gz',
                'log_file_name': uid+'_'+str(i)+'.log',
            })
            print(f'插入数据成功：{uid}_{i}')
    db.close()

    sftp = LogSFTP()
    sftp.send_file(f'./data/sim/{uid}/{uid}.tar.gz', f'/home/damage_sim_log/{uid}.tar.gz')
    print('日志压缩包上传成功')
