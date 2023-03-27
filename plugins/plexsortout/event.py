import logging
from typing import Dict

from flask import Blueprint, request
from mbot.common.flaskutils import api_result
import json
import time
import threading
# from plexapi.server import PlexServer

from mbot.core.event.models import EventType
from mbot.core.plugins import PluginContext,PluginMeta,plugin
from . import plexst
from .get_top250 import get_top250_config

_LOGGER = logging.getLogger(__name__)
plugins_name = '「PLEX 工具箱」'

plex_webhook = Blueprint('get_plex_event', __name__)
"""
把flask blueprint注册到容器
这个URL访问完整的前缀是 /api/plugins/你设置的前缀
"""
plugin.register_blueprint('get_plex_event', plex_webhook)

@plugin.after_setup
def after_setup(plugin: PluginMeta, plugin_conf: dict):
    """
    插件加载后执行的操作
    """
    _LOGGER.info(f'{plugins_name}插件开始加载')
    # global added, libtable , plex_url, plex_token
    global added, libtable
    added = plugin_conf.get('Added') if plugin_conf.get('Added') else None
    if added:
        _LOGGER.info(f'{plugins_name}使用「PLEX 入库事件」作为触发运行')
    else:
        _LOGGER.info(f'{plugins_name}使用「Mbot 下载完成事件」作为触发运行')
    libstr = plugin_conf.get('LIBRARY')
    if libstr:
        libtable=libstr.split(',')
        _LOGGER.info(f'{plugins_name}需要整理的库：{libtable}')
        plugin_conf['library']=libtable
    else:
        _LOGGER.info(f'{plugins_name}未设置需要整理的媒体库名称')
        plugin_conf['library'] = 'ALL'
    
    # plex_url = plugin_conf.get('plex_url')
    # plex_token = plugin_conf.get('plex_token')
    # plex = PlexServer(plex_url, plex_token)

    # # 开启webhooks
    # settings = plex.settings
    # if not settings._settings['webHooksEnabled'].value:
    #     _LOGGER.info(f"{plugins_name}PLEX 的 webhook 开关未打开，将自动打开！")
    #     settings._settings['webHooksEnabled'].set(True)
    #     plex.settings.save()
    # else:
    #     _LOGGER.info(f"{plugins_name}PLEX 的 webhook 开关已打开")
    
    # 传递设置参数
    get_top250_config(plugin_conf)
    plexst.setconfig(plugin_conf)
    _LOGGER.info(f'{plugins_name}自定义参数加载完成')
    # printAllMembers(plexst)

@plugin.config_changed
def config_changed(plugin_conf: dict):
    """
    插件变更配置后执行的操作
    """
    _LOGGER.info(f'{plugins_name}配置发生变更，加载新配置')
    global added, libtable
    added = plugin_conf.get('Added') if plugin_conf.get('Added') else None
    if added:
        _LOGGER.info(f'{plugins_name}使用「PLEX 入库事件」作为触发运行')
    else:
        _LOGGER.info(f'{plugins_name}使用「Mbot 下载完成事件」作为触发运行')
    libstr = plugin_conf.get('LIBRARY')
    if libstr:
        libtable=libstr.split(',')
        _LOGGER.info(f'{plugins_name}需要整理的库：{libtable}')
        plugin_conf['library']=libtable
    else:
        _LOGGER.info(f'{plugins_name}未设置需要整理的媒体库名称')
        plugin_conf['library'] = 'ALL'
    
    # plex_url = plugin_conf.get('plex_url')
    # plex_token = plugin_conf.get('plex_token')
    # plex = PlexServer(plex_url, plex_token)
    
    # # 开启webhooks
    # settings = plex.settings
    # if not settings._settings['webHooksEnabled'].value:
    #     _LOGGER.info(f"{plugins_name}PLEX 的 webhook 开关未打开，将自动打开！")
    #     settings._settings['webHooksEnabled'].set(True)
    #     plex.settings.save()
    # else:
    #     _LOGGER.info(f"{plugins_name}PLEX 的 webhook 开关已打开")
    
    # 传递设置参数
    get_top250_config(plugin_conf)
    plexst.setconfig(plugin_conf)
    _LOGGER.info(f'{plugins_name}自定义参数加载完成')
    # printAllMembers(plexst)

def printAllMembers(cls):
    print('\n'.join(dir(cls)))

last_event_time = 0
last_event_count = 1
# 接收 plex 服务器主动发送的事件
# @login_required() # 若要接口access_key鉴权，则取消注释 
@plex_webhook.route('/webhook', methods=['POST'])
def webhook():
    global last_event_time, last_event_count
    payload = request.form['payload']
    data = json.loads(payload)
    # plex_event = data['event']
    plex_event = data.get('event', '')
    # if plex_event in ['library.on.deck', 'library.new', 'media.play', 'media.pause', 'media.resume'] and added:
    if plex_event in ['library.on.deck', 'library.new'] and added:
        metadata = data.get('Metadata', '')
        library_section_title = metadata.get('librarySectionTitle', '')
        # 媒体库类型：show artist movie photo
        library_section_type = metadata.get('librarySectionType', '')
        rating_key = metadata.get('ratingKey', '')
        parent_rating_key = metadata.get('parentRatingKey', '')
        grandparent_rating_key = metadata.get('grandparentRatingKey', '')
        grandparent_title = metadata.get('grandparentTitle', '')
        parent_title = metadata.get('parentTitle', '')
        org_title = metadata.get('title', '')
        org_type = metadata.get('type', '')

        # 如果是照片库直接跳过
        if library_section_type == 'photo': return api_result(code=0, message=plex_event, data=data)
        _LOGGER.info(f'{plugins_name}接收到 PLEX 通过 Webhook 传过来的「入库事件」，开始分析事件')
        
        # 执行自动整理
        # plexst.process(library_section_title)
        # thread = threading.Thread(target=lambda: plexst.process(library_section_title))
        thread = threading.Thread(target=plexst.process_new, args=(library_section_title,rating_key,parent_rating_key,grandparent_rating_key,grandparent_title,parent_title,org_title,org_type))
        thread.start()

        # if time.time() - last_event_time < 75:
        #     last_event_count = last_event_count + 1
        #     _LOGGER.info(f'{plugins_name}75 秒内接收到 {last_event_count} 条入库事件，只处理一次')
        # else:
        #     last_event_time = time.time()
        #     last_event_count = 1
        #     time.sleep(60)
        #     _LOGGER.info(f'{plugins_name}接收到 PLEX 通过 Webhook 传过来的「入库事件」，开始整理')
        #     # 执行自动整理
        #     plexst.process(library_section_title)

    return api_result(code=0, message=plex_event, data=data)

    # plex_event_all = {
    #     'media.pause': '暂停',
    #     'media.play': '开始播放',
    #     'media.resume': '恢复播放',
    #     'media.stop': '停止播放',
    #     'library.on.deck': '新片入库',
    #     'library.new': '新片入库'
    # }

# @plugin.on_event(
#     bind_event=['PlexActivityEvent'], order=1)
# def on_event(ctx: PluginContext, event_type: str, data: Dict):
#     """
#     触发绑定的事件后调用此函数
#     函数接收参数固定。第一个为插件上下文信息，第二个事件类型，第三个事件携带的数据
#     """
#     # _LOGGER.info(f'{plugins_name}接收到「PlexActivityEvent」事件，开始整理')
#     if data.get('Activity') == 'Added' and added:
#         _LOGGER.info(f'{plugins_name}接收到「PLEX 入库」事件，开始整理')
#         plexst.process()
#     # plexst.send_by_event(event_type, data)

@plugin.on_event(
    bind_event=[EventType.DownloadCompleted], order=1)
def on_event(ctx: PluginContext, event_type: str, data: Dict):
    """
    触发绑定的事件后调用此函数
    函数接收参数固定。第一个为插件上下文信息，第二个事件类型，第三个事件携带的数据
    """
    # _LOGGER.info(f'{plugins_name}接收到「DownloadCompleted」事件，现在开始整理')
    if not added:
        _LOGGER.info(f'{plugins_name}接收到「下载完成事件」且未开启入库事件触发，现在开始整理')
        plexst.process()
    else:
        _LOGGER.info(f'{plugins_name}接收到「下载完成事件」但已开启入库事件触发，将等待 PLEX 入库后再整理')
    # plexst.send_by_event(event_type, data)
