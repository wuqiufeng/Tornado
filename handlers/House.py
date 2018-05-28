# coding:utf-8

import logging
import json
import math
import constants


from handlers.BaseHandler import BaseHandler
from utils.response_code import RET
from utils.commons import required_login
from utils.qiniu_storage import storage
from utils.session import Session


class IndexHandler(BaseHandler):
    """主页信息"""
    def get(self):
        self.write(dict(errcode=RET.OK, errmsg="OK"))

class AreaInfoHandler(BaseHandler):
    """提供城区信息"""
    def get(self):
        # 先到redis中查询数据,如果获取到数据,直接返回给用户
        try:
            ret = self.redis.get('area_info')
        except Exception as e:
            logging.error(e)
            ret = None
        #logging.info(ret)
        if ret:
            # 回传JSON格式响应数据
            logging.info("hit redis: area_info")
            resp = '{"errcode":"0", "errmsg":"OK", "data":%s}'%ret
            return self.write(resp)


        logging.info(resp)
        try:
            sql = "select ai_area_id, ai_name from ih_area_info"
            ret = self.db.query(sql)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="数据库查询出错"))
        if not ret:
            return self.write(dict(errcode=RET.NODATA, errmsg="没有数据"))

        data = []
        for row in ret:
            d = {
                    "area_id":row.get('ai_area_id', ''),
                    "name":row.get('ai_name', '')
                    }
            data.append(d)

        json_data = json.dumps(data)
        try:
            self.redis.setex("area_info", constants.REDIS_AREA_INFO_EXPIRES_SECONDES,
                    json_data)
        except Exception as e:
            logging.error(e)

        logging.info(data)
        self.write(dict(errcode=RET.OK, errmsg="OK", data=data))


class HouseInfoHandler(BaseHandler):
    @required_login
    def post(self):
        """保持发布的房源"""
         # 获取参数
        """
        {
            "title":"",
            "price":"",
            "area_id":"1",
            "address":"",
            "room_count":"",
            "acreage":"",
            "unit":"",
            "capacity":"",
            "beds":"",
            "deposit":"",
            "min_days":"",
            "max_days":"",
            "facility":["7","8"]
        }
        """
        user_id = self.session.data.get("user_id")
        title = self.json_args.get("title")
        price = self.json_args.get("price")
        area_id = self.json_args.get("area_id")
        address = self.json_args.get("address")
        room_count = self.json_args.get("room_count")
        acreage = self.json_args.get("acreage")
        unit = self.json_args.get("unit")
        capacity = self.json_args.get("capacity")
        beds = self.json_args.get("beds")
        deposit = self.json_args.get("deposit")
        min_days = self.json_args.get("min_days")
        max_days = self.json_args.get("max_days")
        facility = self.json_args.get("facility") # 对一个房屋的设施，是列表类型

        #校验
        if not all((title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days)):
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))

        try:
            price = int(price)*100
            deposit = int(deposit)*100
        except Exception as e:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="参数错误"))

        # 数据
        try:
            sql = "insert into ih_house_info(hi_user_id,hi_title,hi_price,hi_area_id,hi_address,hi_room_count," \
                    "hi_acreage,hi_house_unit,hi_capacity,hi_beds,hi_deposit,hi_min_days,hi_max_days) " \
                    "values(%(user_id)s,%(title)s,%(price)s,%(area_id)s,%(address)s,%(room_count)s,%(acreage)s," \
                    "%(house_unit)s,%(capacity)s,%(beds)s,%(deposit)s,%(min_days)s,%(max_days)s)"
                    # 对于insert语句，execute方法会返回最后一个自增id
            house_id = self.db.execute(sql, user_id=user_id, title=title, price=price, area_id=area_id, address=address,\
                    room_count=room_count, acreage=acreage, house_unit=unit, capacity=capacity,\
                    beds=beds, deposit=deposit, min_days=min_days, max_days=max_days)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="save data error"))

    def get(self):
        """获取房屋信息"""
        session = Session(self)
        user_id = session.data.get("user_id", "-1")
        house_id = self.get_argument("house_id")
        # 校验参数
        if not house_id:
            return self.write(dict(errcode=RET.PARAMERR, errmsg="缺少参数"))

        # 先从redis缓存中获取信息
        try:
            ret = self.redis.get("house_info_%s" % house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        if ret:
            # 此时从redis中获取到的是缓存的json格式数据
            resp = '{"errcode":"0", "errmsg":"OK", "data":%s, "user_id":%s}' % (ret, user_id)
            return self.write(resp)

        # 查询房屋基本信息
        sql = "select hi_title,hi_price,hi_address,hi_room_count,hi_acreage,hi_house_unit,hi_capacity,hi_beds," \
                "hi_deposit,hi_min_days,hi_max_days,up_name,up_avatar,hi_user_id " \
                "from ih_house_info inner join ih_user_profile on hi_user_id=up_user_id where hi_house_id=%s"
        try:
            ret = self.db.get(sql, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="查询错误"))

        # 用户查询的可能是不存在的房屋id, 此时ret为None
        if not ret:
            return self.write(dict(errcode=RET.NODATA, errmsg="查无此房"))

        data = {
            "hid":house_id,
            "user_id":ret["hi_user_id"],
            "title":ret["hi_title"],
            "price":ret["hi_price"],
            "address":ret["hi_address"],
            "room_count":ret["hi_room_count"],
            "acreage":ret["hi_acreage"],
            "unit":ret["hi_house_unit"],
            "capacity":ret["hi_capacity"],
            "beds":ret["hi_beds"],
            "deposit":ret["hi_deposit"],
            "min_days":ret["hi_min_days"],
            "max_days":ret["hi_max_days"],
            "user_name":ret["up_name"],
            "user_avatar":constants.QINIU_URL_PREFIX + ret["up_avatar"] if ret.get("up_avatar") else ""
        }

        # 查询房屋的图片
        sql = "select hi_url from ih_house_image where hi_house_id=%s"
        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None

        # 如果查询到的图片
        images = []
        if ret:
            for image in ret:
                images.append(constants.QINIU_URL_PREFIX + image["hi_url"])
        data["images"] = images

        # 查询房屋的基本设施
        sql = "select hf_facility_id from ih_house_facility where hf_house_id=%s"
        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None

        # 如果查询到设施
        facilities = []
        if ret:
            for facility in ret:
                facilities.append(facility["hf_facility_id"])
        data["facilities"] = facilities

        # 查询评论信息
        sql = "select oi_comment,up_name,oi_utime,up_mobile from ih_order_info inner join ih_user_profile " \
                "on oi_user_id=up_user_id where oi_house_id=%s and oi_status=4 and oi_comment is not null"
        try:
            ret = self.db.query(sql, house_id)
        except Exception as e:
            logging.error(e)
            ret = None
        comments = []
        if ret:
            for comment in ret:
                comments.append(dict(
                    user_name = comment["up_name"] if comment["up_name"] != comment["up_mobile"] else "匿名用户",
                    content = comment["oi_comment"],
                    ctime = comment["oi_utime"].strftime("%Y-%m-%d %H:%M:%S")
                ))
        data["comments"] = comments

        # 存入到redis中
        json_data = json.dumps(data)
        try:
            self.redis.setex("house_info_%s" % house_id, constants.REDIS_HOUSE_INFO_EXPIRES_SECONDES,json_data)
        except Exception as e:
            logging.error(e)

        resp = '{"errcode":"0", "errmsg":"OK", "data":%s, "user_id":%s}' % (json_data, user_id)
        # self.write(dict(errcode=RET.OK, errmsg="OK", data=data))
        self.write(resp)


class HouseImageHandler(BaseHandler):
    """房屋照片"""
    @required_login
    def post(self):
        user_id = self.session.data['user_id']
        house_id = self.get_argument('house_id')
        house_image = self.request.files['house_image'][0]['body']

        # 上传七牛图片
        img_name = storage(house_image)
        if not img_name:
            return self.write(dict(errcode=RET.THIRDERR, errmsg="qiniu error"))
        try:
            # 保存图片路径到数据库ih_house_image表,并且设置房屋的主图片(ih_house_info中的hi_index_image_url
            # 将用户上传的第一张图片作为房屋的主图片
            sql = "insert into ih_house_image(hi_house_id,hi_url) values(%s,%s);" \
                    "update ih_house_info set hi_index_image_url=%s \
                    where hi_house_id=%s and hi_index_image_url is null;"

            logging.info(sql)
            self.db.execute(sql, house_id, img_name, img_name, house_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="upload failed"))
        img_url = constants.QINIU_URL_PERFIX + img_name
        self.write(dict(errcode=RET.OK, errmsg="OK", url=img_url))


class MyHousesHandler(BaseHandler):
    """个人房源"""
    @required_login
    def get(self):
        user_id = self.session.data['user_id']
        logging.info(user_id)
        try:
            sql = "select a.hi_house_id, a.hi_title, a.hi_price, a.hi_ctime, b.ai_name, a.hi_index_image_url \
                    from ih_house_info a inner join ih_area_info b on a.hi_area_id=b.ai_area_id where a.hi_user_id=%(user_id)s;"
            ret = self.db.query(sql, user_id=user_id)
        except Exception as e:
            logging.error(e)
            return self.write(dict(errcode=RET.DBERR, errmsg="get data error"))
        logging.info(sql)
        houses = []
        if ret:
            for l in ret:
                house = {
                    "house_id":l['hi_house_id'],
                    "title":l["hi_title"],
                    "price":l["hi_price"],
                    "ctime":l["hi_ctime"].strftime("%Y-%m-%d"),
                    "area_name":l['ai_name'],
                    "img_url":constants.QINIU_URL_PREFIX + l["hi_index_image_url"] if l["hi_index_image_url"] else ""
                }
                houses.append(house)
        logging.info(houses)
        self.write(dict(errcode=RET.OK, errmsg="OK", houses=houses))


class HouseListHandler(BaseHandler):
    """房源列表页面"""
    def get(self):
        pass
