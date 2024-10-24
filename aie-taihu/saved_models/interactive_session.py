#!/usr/bin/env python
# -*- coding: utf-8 -*-

from aiearth.core.client.endpoints import *
from .client import *
from aiearth.core import g_var
import time
from aiearth.core.error.aie_error import *
from aiearth import engine


class InteractiveSessionClient(BaseClient):
    class ResponseCode(object):
        OK = 0

    @staticmethod
    def post(url, reqeust_data, append_extra_hdrs=True):
        headers = {"Content-Type": "application/json"}
        resp = super(InteractiveSessionClient,
                     InteractiveSessionClient).post(url, headers, reqeust_data, append_extra_hdrs)
        response_data = resp.json()

        if "code" in response_data and response_data["code"] == InteractiveSessionClient.ResponseCode.OK:
            return response_data["payload"]
        else:
            extrainfo = {}
            if "taskId" in reqeust_data:
                extrainfo["taskId"] = reqeust_data["taskId"]
            raise AIEError(response_data["code"], response_data["msg"], json.dumps(extrainfo))

    @staticmethod
    def get(url, append_extra_hdrs=True):
        headers = {"Content-Type": "application/json"}
        resp = super(InteractiveSessionClient,
                     InteractiveSessionClient).get(url, headers, append_extra_hdrs)
        data = resp.json()
        if "code" in data and data["code"] == InteractiveSessionClient.ResponseCode.OK:
            return data["payload"]
        else:
            raise AIEError(data["code"], data["msg"])


class InteractiveSession():
    class SessionStatus(object):
        NOT_STARTED = "not_started"
        RECOVERING = "recovering"
        STARTING = "starting"

        IDLE = "idle"
        BUSY = "busy"
        SUCCESS = "success"

        SHUTTING_DOWN = "shutting_down"
        ERROR = "error"
        DEAD = "dead"
        KILLED = "killed"

    @staticmethod
    def create(enable_udf=False):
        data = {
            "enableUdf": "true" if enable_udf else "false"
        }

        url = Endpoints.INTERACTIVE_SESSION + InteractiveSessionResource.CREATE
        payload = InteractiveSessionClient.post(url, data, True)
        session_id = payload["id"]

        print("计算资源初始化中，请等待...", end="")
        status = InteractiveSession.status(session_id)
        while InteractiveSession.isStarting(status):
            # print(f"interactive session create status: {status}")
            time.sleep(5)
            print(".", end="")
            status = InteractiveSession.status(session_id)
        print("")
        if not InteractiveSession.isActive(status):
            raise AIEError(AIEErrorCode.ENVIRONMENT_INIT_ERROR,
                           f"计算资源初始化失败. status: {status}")
        g_var.set_var(
            g_var.GVarKey.InteractiveSession.INTERACTIVE_SESSION_ID, session_id)

    @staticmethod
    def status(session_id):
        url = Endpoints.INTERACTIVE_SESSION + \
            InteractiveSessionResource.QUERY.format(session_id)
        payload = InteractiveSessionClient.get(url)
        return payload

    @staticmethod
    def isStarting(status):
        return status["state"] in (InteractiveSession.SessionStatus.NOT_STARTED, InteractiveSession.SessionStatus.STARTING, InteractiveSession.SessionStatus.RECOVERING)

    @staticmethod
    def isActive(status):
        return status["state"] in (InteractiveSession.SessionStatus.IDLE, InteractiveSession.SessionStatus.BUSY, InteractiveSession.SessionStatus.SUCCESS)

    @staticmethod
    def isDead(status):
        return status["state"] in (InteractiveSession.SessionStatus.SHUTTING_DOWN, InteractiveSession.SessionStatus.ERROR, InteractiveSession.SessionStatus.DEAD, InteractiveSession.SessionStatus.KILLED)

    @staticmethod
    def active(session_id):
        status = InteractiveSession.status(session_id)
        return InteractiveSession.isActive(status)

    @staticmethod
    def getCurrentSessionId():
        if not g_var.has_var(g_var.GVarKey.InteractiveSession.INTERACTIVE_SESSION_ID):
            raise AIEError(AIEErrorCode.DEFAULT_INTERNAL_ERROR,
                           "", f'''服务端SessionID获取失败，请先调用
import aie
aie.Authenticate()
aie.Initialize() 
进行授权及初始化''')
        return g_var.get_var(g_var.GVarKey.InteractiveSession.INTERACTIVE_SESSION_ID)

    @staticmethod
    def cancelAllJobs():
        data = {
            "sessionId": InteractiveSession.getCurrentSessionId()
        }

        url = Endpoints.INTERACTIVE_SESSION + InteractiveSessionResource.CANCEL_ALL
        InteractiveSessionClient.post(url, data, True)

    @staticmethod
    def getInfo(obj):
        if isinstance(obj, (engine.Image, engine.Feature)) \
                and obj.func_name is None \
                and obj.invoke_args is None \
                and '_MAPPING_VAR' in obj.var_name:
            raise AIEError(AIEErrorCode.ARGS_ERROR, "请勿在map函数中使用getInfo方法",
                           "请尝试使用for循环逐个获取，https://engine-aiearth.aliyun.com/docs/page/api?d=9e276c")
        expr = engine.serialize.serializer.encode(obj)
        options = {
            "taskType": "getInfo"
        }
        task_id = newUUID()
        data = {
            "taskId": task_id,
            "sessionId": InteractiveSession.getCurrentSessionId(),
            "script": "{\"expression\":" + expr + "}",
            "options": json.dumps(options)
        }

        url = Endpoints.INTERACTIVE_SESSION + InteractiveSessionResource.EXEC
        payload = InteractiveSessionClient.post(url, data)

        # print("payload", json.dumps(payload))

        if payload["state"] == "cancelled":
            raise AIEError(AIEErrorCode.JOB_CANCELLED, "该任务已取消")

        if payload["state"] != "success":
            extrainfo = {}
            if "taskId" in data:
                extrainfo["taskId"] = data["taskId"]
            raise AIEError(payload["output"]["error_code"],
                           payload["output"]["error_message"], json.dumps(extrainfo))
        return payload["output"]["data"]["application/json"]

    @staticmethod
    def getBounds(obj):
        if isinstance(obj, (engine.Image, engine.Feature)) \
                and obj.func_name is None \
                and obj.invoke_args is None \
                and '_MAPPING_VAR' in obj.var_name:
            raise AIEError(AIEErrorCode.ARGS_ERROR, "请勿在map函数中使用getBounds方法",
                           "请尝试使用for循环逐个获取，https://engine-aiearth.aliyun.com/docs/page/api?d=9e276c")
        expr = engine.serialize.serializer.encode(obj)
        options = {
            "taskType": "getBounds"
        }
        task_id = newUUID()
        data = {
            "taskId": task_id,
            "sessionId": InteractiveSession.getCurrentSessionId(),
            "script": "{\"expression\":" + expr + "}",
            "options": json.dumps(options)
        }

        url = Endpoints.INTERACTIVE_SESSION + InteractiveSessionResource.EXEC
        payload = InteractiveSessionClient.post(url, data)

        # print("payload", json.dumps(payload))
        
        if payload["state"] == "cancelled":
            raise AIEError(AIEErrorCode.JOB_CANCELLED, "该任务已取消")

        if payload["state"] != "success":
            extrainfo = {}
            if "taskId" in data:
                extrainfo["taskId"] = data["taskId"]
            raise AIEError(payload["output"]["error_code"],
                           payload["output"]["error_message"], json.dumps(extrainfo))
        return payload["output"]["data"]["application/json"]

    @staticmethod
    def classifierTrain(obj):
        expr = engine.serialize.serializer.encode(obj)
        options = {
            "taskType": "getResult"
        }
        task_id = newUUID()
        data = {
            "taskId": task_id,
            "sessionId": InteractiveSession.getCurrentSessionId(),
            "script": "{\"expression\":" + expr + "}",
            "options": json.dumps(options)
        }

        url = Endpoints.INTERACTIVE_SESSION + InteractiveSessionResource.EXEC
        payload = InteractiveSessionClient.post(url, data)
        if payload["state"] == "cancelled":
            raise AIEError(AIEErrorCode.JOB_CANCELLED, "该任务已取消")

        if payload["state"] != "success":
            extrainfo = {}
            if "taskId" in data:
                extrainfo["taskId"] = data["taskId"]
            raise AIEError(payload["output"]["error_code"],
                           payload["output"]["error_message"], json.dumps(extrainfo))
        return payload["output"]["data"]["application/json"]
