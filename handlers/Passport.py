# coding:utf-8

import logging
import re
import hashlib
import config

from handlers.BaseHandler import BaseHandler
from utils.session import Session
from utils.response_code import RET
from utils.commons import required_login

class RegisterHandler(BaseHandler):
	"""注册"""
	def post(self):
            # 获取参数
            mobile = self.json_args.get("mobile")
            sms_code = self.json_args.get("phonecode")
            password = self.json_args.get("password")

            # 检查参数
            if not all((mobile, sms_code, password)):
                return self.write(dict(errcode=RET.PARAMERR, errmsg="参数不完整"))

            if not re.match(r"1\d{10}$", mobile):
                return self.write(dict(errcode=RET.DATAERR, errmsg="手机号错误"))

            # 方便调试
            if "2468" != sms_code:
                try:
                    real_sms_code = self.redis.get("sms_code_%s" % mobile)
                except Exception as e:
                    logging.error(e)
                    return self.write(dict(errcode=RET.DBERR, errmsg="查询验证码出错"))

                if not real_sms_code:
                    return self.write(dict(errcode=RET.NODATA, errmsg="验证码过期"))

                if real_sms_code != sms_code:
                    return self.write(dict(errcode=RET.DATAERR, errmsg="验证码错误"))

                # 删除redis中sms_code
                try:
                    self.redis.delete("sms_code_%s" % mobile)
                except Exception as e:
                    logging.error(e)

            # 保持用户信息
            passwd = hashlib.sha256(password+config.passwd_hash_key).hexdigest()
            sql = "insert into ih_user_profile(up_name, up_mobile, up_passwd) values(%(name)s, %(mobile)s, %(passwd)s);"

            try:
                user_id = self.db.execute(sql, name=mobile,mobile=mobile,passwd=passwd)
            except Exception as e:
                logging.error(e)
                return self.write(dict(errcode=RET.DATAEXIST, errmsg="手机号已存在"))
            
            # 用session记录用户登陆状态
            session = Session(self)
            session.data["user_id"] = user_id
            session.data["mobile"] = mobile
            session.data["name"] = mobile

            try:
                session.save()
            except Exception as e:
                logging.error(e)

            self.write(dict(errcode=RET.OK, errmsg="注册成功"))


class LoginHandler(BaseHandler):
	"""登录"""
	def post(self):
            mobile = self.json_args.get("mobile")
            password = self.json_args.get("password")

            # 检查参数
            if not all((mobile, password)):
                return self.write(dict(errcode=RET.PARAMERR, errmsg="参数不完整"))

            if not re.match(r"1\d{10}$", mobile):
                return self.write(dict(errcode=RET.DATAERR, errmsg="手机号错误"))

            sql = "select up_user_id, up_name, up_passwd from ih_user_profile where up_mobile=%(mobile)s"
            res = self.db.get(sql, mobile=mobile)
            password = hashlib.sha256(password + config.passwd_hash_key).hexdigest()
            if res and res["up_passwd"] == unicode(password):
                # 生成session数据
                try:
                    self.session=Session(self)
                    self.session.data['user_id'] = res['up_user_id']
                    self.session.data['name'] = res['up_name']
                    self.session.data['mobile'] = mobile
                    self.session.save()
                except Exception as e:
                    logging.error(e)
                    
                return self.write(dict(errcode=RET.OK, errmsg="OK"))
            else:
                return self.write(dict(errcode=RET.DATAERR, errmsg="手机号或密码错误"))


class LogoutHandler(BaseHandler):
	"""退出登录"""
        @required_login
	def get(self):
            self.session.clear()
            self.write(dict(errcode=RET.OK, errmsg="退出成功"))

class CheckLoginHandler(BaseHandler):
	"""检查登陆状态"""
	def get(self):
            if self.get_current_user():
                self.write(dict(errcode=RET.OK, errmsg="true", data=dict(name=self.session.data.get("name"))))
            else:
                self.write(dict(errcode=RET.SESSIONERR, errmsg="false"))
