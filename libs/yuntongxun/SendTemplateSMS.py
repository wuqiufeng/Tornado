#-*- coding: UTF-8 -*-  

from CCPRestSDK import REST
import ConfigParser
import logging

#主帐号
accountSid= '8aaf0708635e4ce0016364282af103a9';

#主帐号Token
accountToken= '03b65c6092c148adaa0e651e8bde5c9b';

#应用Id
appId='8aaf0708635e4ce0016364282b5403b0';

#请求地址，格式如下，不需要写http://
serverIP='app.cloopen.com';

#请求端口 
serverPort='8883';

#REST版本号
softVersion='2013-12-26';

# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id
class CCP(object):
    def __init__(self):
        self.rest = REST(serverIP,serverPort,softVersion)
        self.rest.setAccount(accountSid,accountToken)
        self.rest.setAppId(appId)

    @staticmethod
    def instance():
        if not hasattr(CCP, "_instance"):
            CCP._instance = CCP()
        return CCP._instance

    def sendTemplateSMS(self, to, datas, tempId):
        try:
            result = self.rest.sendTemplateSMS(to, datas, tempId)
        except Exception as e:
            logging.error(e)
            raise e

        #for k,v in result.iteritems(): 
        #    if k=='templateSMS' :
        #        for k,s in v.iteritems(): 
        #            print '%s:%s' % (k, s)
        #    else:
        #        print '%s:%s' % (k, v)

        if result.get("statusCode") == "000000":
            return True
        else:
            return False

ccp = CCP.instance()

if __name__ == "__main__":
    ccp = CCP.instance()
    ccp.sendTemplateSMS("18964035205", ["1234", 5], 1)

#sendTemplateSMS(手机号码,内容数据,模板Id)

