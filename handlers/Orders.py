# coding:utf-8

import logging
import constants

from handlers.BaseHandler import BaseHandler
from utils.commons import required_login
from utils.response_code import RET

class OrderHandler(BaseHandler):
    """订单"""
    @required_login
    def post(self):
        pass

class MyOrdersHandler(BaseHandler):
    """我的订单"""
    def get(self):
        pass

class AcceptOrderHandler(BaseHandler):
    """接单"""
    @required_login
    def post(self):
        pass

class RejectOrderHandler(BaseHandler):
    """拒单"""
    @required_login
    def post(self):
        pass

class OrderCommentHandler(BaseHandler):
    """评论"""
    @required_login
    def post(self):
        pass
