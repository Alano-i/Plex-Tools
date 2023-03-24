from mbot.core.plugins import plugin, PluginCommandContext, PluginCommandResponse,PluginMeta
from . import plexst
from mbot.openapi import mbot_api
from mbot.core.params import ArgSchema, ArgType
from .get_top250 import get_top250
import logging

server = mbot_api
_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
plugins_name = '「PLEX 工具箱」'

def get_enum_data():
    """
    返回一个包含name和value的枚举数据，在前端页面会呈现为下拉列表框；
    value就是你最终你能接收到的变量值
    """
    _LOGGER.info(f'{plugins_name}开始获取媒体库')
    libtable=plexst.get_library()
    return libtable

is_lock_list = [
    {
        "name": "🟢 执行设置中选中的全部操作",
        "value": "run_all"
    },
    {
        "name": "🔒 仅运行【锁定】海报和背景",
        "value": "run_locked"
    },
    {
        "name": "🔓 仅运行【解锁】海报和背景",
        "value": "run_unlocked"
    }
]

@plugin.command(name='select_data', title='整理 PLEX 媒体库', desc='自动翻译标签 & 拼音排序 & 添加TOP250标签 & 筛选Fanart封面', icon='HourglassFull',run_in_background=True)
def select_data(ctx: PluginCommandContext,
                library: ArgSchema(ArgType.Enum, '选择需要整理的媒体库', '', enum_values=get_enum_data,multi_value=True),
                threading_num: ArgSchema(ArgType.String, '多线程处理：填线程数量。默认为0，单线程处理', '示例：2000个媒体，设置40，则会启40个线程处理，每个线程处理50个。建议少于100个线程', default_value='0', required=False),
                sortoutNum: ArgSchema(ArgType.String, '整理数量，示例：50，表示只整理最新的50条，留空整理全部', '', default_value='ALL', required=False),
                is_lock: ArgSchema(ArgType.Enum, '选择需要执行的操作，留空执行设置中选中的全部操作', '', enum_values=lambda: is_lock_list, default_value='run_all', multi_value=False, required=False)):
    # plexst.config['library']=library
    # plexst.process()
    threading_num = int(threading_num)
    plexst.process_all(library,sortoutNum,is_lock,threading_num)
    user_list = list(filter(lambda x: x.role == 1, mbot_api.user.list()))
    if user_list:
        for user in user_list:
            if is_lock == 'run_all':
                mbot_api.notify.send_system_message(user.uid, '手动运行整理 PLEX 媒体库', '翻译标签 && 拼音排序 && 添加TOP250标签完毕 && 筛选Fanart封面')
            else:
                mbot_api.notify.send_system_message(user.uid, '手动运行整理 PLEX 媒体库', '锁定 PLEX 海报和背景完毕')
    return PluginCommandResponse(True, f'手动运行整理 PLEX 媒体库完成')
    
@plugin.command(name='get_top250', title='更新 TOP250 列表', desc='获取最新豆瓣和IMDB TOP250 列表', icon='MovieFilter', run_in_background=True)
def get_top250_echo(ctx: PluginCommandContext):
    _LOGGER.info(f'{plugins_name}开始手动获取最新 TOP250 列表')
    get_top250()
    _LOGGER.info(f'{plugins_name}手动获取最新 TOP250 列表完成')

# @plugin.command(name='plexcollection', title='Plex整理合集首字母', desc='自动整理合集首字母', icon='HourglassFull',run_in_background=True)
# def echo_c(ctx: PluginCommandContext):
#     plexst.process_collections()
#     user_list = list(filter(lambda x: x.role == 1, mbot_api.user.list()))
#     if user_list:
#         for user in user_list:
#             mbot_api.notify.send_system_message(user.uid, 'Plex整理合集首字母',
#                                                 '自动整理合集首字母')
#     return PluginCommandResponse(True, f'Plex合集整理完成')

