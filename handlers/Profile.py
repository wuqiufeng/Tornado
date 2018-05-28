# coding:utf-8

import logging
import constants

from handlers.BaseHandler import BaseHandler
from utils.commons import required_login
from utils.response_code import RET
from utils.qiniu_storage import storage

class ProfileHandler(BaseHandler):
    """个人信息"""
    @required_login
    def get(self):
        user_id = self.session.data['user_id']
        try:
            sql = "select up_name,up_mobile,up_avatar from ih_user_profile where up_user_id=%(user_id)s"
            ret = self.db.get(sql, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="get data error"))
        if ret["up_avatar"]:
            img_url = constants.QINIU_URL_PREFIX + ret["up_avatar"]
        else:
            img_url=None
        data=dict(user_id=user_id, name=ret['up_name'], mobile=ret['up_mobile'], avatar=img_url)
        self.write(dict(errcode=RET.OK, errmsg="OK", data=data))

class NameHandler(BaseHandler):
    """用户名"""
    @required_login
    def post(self):
        # 在session中获取用户user_id
        user_id = self.session.data['user_id']
        name = self.json_args.get('name')

        # 判断用户名是否为空
        if name in(None, ""):
            return self.write(dict(errcode="RET.PARAMERR", errmsg="params error"))

        # 保存用户昵称name，并同时判断name是否重复（利用数据库的唯一索引)
        try:
            sql = "update ih_user_profile set up_name=%(name)s where up_user_id=%(user_id)s"
            self.db.execute_rowcount(sql, name=name, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="name has exist"))

        # 修改session数据中name字段
        self.session.data['name'] = name
        try:
            self.session.save()
        except Exception as e:
            logging.error(e)
        self.write(dict(errcode=RET.OK, errmsg="OK"))


class AuthHandler(BaseHandler):
    """实名认证"""
    @required_login
    def get(self):
        # 在session中获取用户user_id
        user_id = self.session.data['user_id']

        try:
            sql = "select up_real_name, up_id_card from ih_user_profile where up_user_id=%(user_id)s"
            ret = self.db.get(sql,user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="get data failed"))
        logging.debug(ret)
        if not ret:
            return self.write(dict(errcode=RET.NODATA, errmsg="no data"))
        data = dict(real_name=ret.get('up_real_name'), id_card=ret.get('up_id_card'))
        self.write(dict(errcode=RET.OK, errmsg="OK", data=data))

    @required_login
    def post(self):
        user_id = self.session.data['user_id']
        real_name = self.json_args.get('real_name')
        id_card = self.json_args.get('id_card')
        if real_name in (None,"") or id_card in (None, ""):
            return self.write(dict(errcode=RET.PARAMERR,errmsg="params error"))
        
        try:
            sql = "update ih_user_profile set up_real_name=%(real_name)s, up_id_card=%(id_card)s where up_user_id=%(user_id)s"
            self.db.execute_rowcount(sql, real_name=real_name, id_card=id_card, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="update failed"))
        self.write(dict(errcode=RET.OK, errmsg="OK"))
    

class AvatarHandler(BaseHandler):
    """上传头像"""
    @required_login
    def post(self):
        files = self.request.files.get('avatar')
        if not files:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="未传图片"))
        avatar = files[0]['body']
        #调用七牛上传文件
        try:
            file_name = storage(avatar)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.THREDERR, errmsg="上传失败"))

        user_id = self.session.data['user_id']

        sql = "update ih_user_profile set up_avatar=%(avatar)s where up_user_id=%(user_id)s"
        try:
            row_count = self.db.execute_rowcount(sql, avatar=file_name, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="保持错误"))
        
        self.write(dict(errcode=RET.OK, errmsg="OK", data="%s%s" %(constants.QINIU_URL_PREFIX, file_name)))


