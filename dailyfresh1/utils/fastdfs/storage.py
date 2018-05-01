from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings

# class FastDFSStorage(Storage):
#     """自定义存储系统，实现django对接fdfs的文件存储，当运维在后台站点上传图片使用"""
#     # """存储类必须实现_open方法和_save方法"""
#     def __init__(self, clinet_conf=None, server_ip=None):
#         """初始化，设置参数"""
#         #可能存在两个参数都是None的情况，判断
#         if clinet_conf is None:
#             # 当外界没有传入client_conf
#             clinet_conf = settings.CLIENT_CONF
#         # 当外界传入了client_conf
#         self.client_conf = clinet_conf
#         if server_ip is None:
#             server_ip = settings.SERVER_IP
#         self.server_ip = server_ip
#     def _open(self):
#         """读取文件时使用"""
#         pass
#     def _save(self,name,content):
#         """ 存储文件时使用，参数2 name是上传来的文件名，参数3是上传来的File对象，
#         content必须是一个File对象，提供read(),获取文件内容"""
#         #1.创建fdfs客户端对象 --- 参数是 client_conf文件的路径
#         client = Fdfs_client(self.client_conf)
#         #2.获取要上传的文件内容
#         file_data = content.read()
#         #3.调用上传的方法，并且接收返回值,为防止报异常放在try中
#         try:
#             ret = client.upload_by_buffer(file_data)
#         except Exception as e:
#             print(e)#方便自己调试bug
#             raise
#         #4.根据返回的数据，判断是否上传成功
#         if ret.get('Status')== 'Upload successed.':
#             # 如果上传成功，就获取file_id
#             file_id = ret.get('Remote file_id')
#             # 存储file_id:只需要返回file_id,我们的client,会自动的检测当前站点中正在使用的模型类,然后存储进去
#             # 如果当前运维在操作GoodsSKU模型类,上传图片,那么return file_id,会自动存储到GoodsSKU模型类对应的数据库表中
#             return file_id
#         else:
#              # 开发工具类时，出现异常不要擅自处理，交给使用者处理
#             raise Exception('上传文件到Fastdfs失败')
#
#     def exists(self,name):
#         """django用来判断文件是否存在的"""
#         #由于是在Fastdfs上存储文件，所以永远返回False
#         return False
#
#     def url(self,name):
#         """用于返回图片在服务器上完整的地址"""
#         return self.server_ip + name


#第二遍
# from django.core.files.storage import Storage
# from django.conf import settings
# from fdfs_client.client import Fdfs_client
# class FastDFSStorage(Storage):
#     """自定义存储系统"""
#     def __init__(self,client_conf=None,server_ip=None):
#         """初始化属性"""
#         if client_conf is None:
#             client_conf = settings.CLIENT_CONF
#         self.client_conf = client_conf
#         if server_ip is None:
#             server_ip = settings.SERVER_IP
#         self.server_ip = server_ip
#     def _open(self, name, mode='rb'):
#         pass
#     def _save(self,name,content):
#         #1.创建client对象
#         client = Fdfs_client(self.client_conf)
#         #2.获取要上传的文件内容
#         file_data = content.read()
#         #3.调用上传方法，接收返回值含有file_id
#         try:
#           ret = client.upload_by_buffer(file_data)
#         except Exception as e:
#             print(e)
#             raise
#         #4.判断上传是否成功，成功就获取file_id,返回给django存储起来即可
#         if ret.get('Status') == ('Upload successed.'):
#             file_id = ret.get('Remote file_id')
#             return file_id
#         else:
#             raise  Exception('上传文件到FastDFS失败')
#
#
#     def exists(self, name):
#         return False
#
#     def url(self, name):
#         """用于返回图片在服务器上完整的地址：server_ip+path"""
#         return self.server_ip + name
from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client

class FastDFSStorage(Storage):
    """自定义文件存储系统"""
    def __init__(self,client_conf=None,server_ip=None):
        if client_conf is None:
            client_conf = settings.CLIENT_CONF
        self.client_conf = client_conf
        if server_ip is None:
            server_ip = settings.SERVER_IP
        self.server_ip = server_ip
    def _open(self,name,mode='rb'):
        pass
    def _save(self,name,content):
        #1.创建fdfs客户端对象
        client = Fdfs_client(self.client_conf)
        #2.获取文件内容
        file_data = content.read()
        #3.调用上传方法，上传文件，放在try中
        try:
           ret = client.upload_by_buffer(file_data)
        except Exception as e:
            print(e)
            raise
        #4.判断是否上传成功，成功就获取file_id返回
        if ret.get('Status') == 'Upload successed.':
            file_id = ret.get('Remote file_id')
            return file_id
        else:
            raise Exception('上传文件到FastDFS失败')

    def exists(self, name):
        return False

    def url(self, name):
        return self.server_ip + name



