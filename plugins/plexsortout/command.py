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
    # _LOGGER.info(f'libtable:{libtable}')
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

collection_on_list = [
    {
        "name": "✅ 开启",
        "value": 'on'
    },
    {
        "name": "📴 关闭",
        "value": 'off'
    }
]
spare_flag_list = [
    {
        "name": "✅ 开启",
        "value": 'on'
    },
    {
        "name": "📴 关闭",
        "value": 'off'
    }
]

@plugin.command(name='select_data', title='整理 PLEX 媒体库', desc='自动翻译标签 & 拼音排序 & 添加TOP250标签 & 筛选Fanart封面', icon='MovieFilter',run_in_background=True)
def select_data(ctx: PluginCommandContext,
                library: ArgSchema(ArgType.Enum, '选择需要整理的媒体库', '', enum_values=get_enum_data,multi_value=True),
                threading_num: ArgSchema(ArgType.String, '多线程处理：填线程数量。默认为0，单线程处理', '示例：2000个媒体，设置40，则会启40个线程处理，每个线程处理50个。建议少于100个线程', default_value='0', required=False),
                sortoutNum: ArgSchema(ArgType.String, '整理数量，10 或 10-50，留空整理全部', '说明：10：整理最新的10个，10-50：整理第10-50个（入库时间排序）', default_value='ALL', required=False),
                is_lock: ArgSchema(ArgType.Enum, '选择需要执行的操作，留空执行设置中选中的全部操作', '', enum_values=lambda: is_lock_list, default_value='run_all', multi_value=False, required=False),
                collection_on_config: ArgSchema(ArgType.Enum, '临时启用合集整理，默认关闭', '', enum_values=lambda: collection_on_list, default_value='off', multi_value=False, required=False),
                spare_flag: ArgSchema(ArgType.Enum, '启用备用整理方案，默认启用', '', enum_values=lambda: spare_flag_list, default_value='on', multi_value=False, required=False)):
    # plexst.config['library']=library
    # plexst.process()
    spare_flag = bool(spare_flag and spare_flag.lower() != 'off')
    collection_on_config = bool(collection_on_config and collection_on_config.lower() != 'off')
    threading_num = int(threading_num)
    plexst.process_all(library,sortoutNum,is_lock,threading_num,collection_on_config,spare_flag)
    user_list = list(filter(lambda x: x.role == 1, mbot_api.user.list()))
    if user_list:
        for user in user_list:
            if is_lock == 'run_all':
                mbot_api.notify.send_system_message(user.uid, '手动运行整理 PLEX 媒体库', '翻译标签 && 拼音排序 && 添加TOP250标签完毕 && 筛选Fanart封面')
            else:
                mbot_api.notify.send_system_message(user.uid, '手动运行整理 PLEX 媒体库', '锁定 PLEX 海报和背景完毕')
    return PluginCommandResponse(True, f'手动运行整理 PLEX 媒体库完成')
    
@plugin.command(name='get_top250', title='更新 TOP250 列表', desc='获取最新豆瓣和IMDB TOP250 列表', icon='MilitaryTech', run_in_background=True)
def get_top250_echo(ctx: PluginCommandContext):
    _LOGGER.info(f'{plugins_name}开始手动获取最新 TOP250 列表')
    # DouBanTop250 = [278, 10997, 13, 597, 101, 637, 129, 424, 27205, 157336, 37165, 28178, 10376, 20453, 5528, 10681, 10775, 269149, 37257, 21835, 81481, 238, 1402, 77338, 43949, 8392, 746, 354912, 31439, 155, 671, 122, 770, 532753, 255709, 14160, 389, 517814, 360814, 4935, 25838, 87827, 51533, 640, 365045, 423, 13345, 10515, 121, 9475, 11216, 804, 490132, 207, 47759, 120, 603, 240, 8587, 242452, 10451, 550, 453, 4922, 14574, 582, 47002, 100, 10867, 15121, 411088, 19995, 857, 510, 21334, 12445, 274, 11324, 120467, 1124, 1954, 23128, 9470, 489, 311, 680, 673, 3082, 18329, 74308, 53168, 2832, 807, 11423, 4977, 22, 672, 152578, 31512, 158445, 25538, 37703, 398818, 142, 162, 197, 16804, 76, 745, 11104, 49026, 128, 177572, 4291, 80, 194, 37185, 161285, 294682, 9559, 51739, 2517, 210577, 30421, 336026, 37797, 1100466, 122906, 594, 10191, 242, 92321, 348678, 10494, 585, 674, 10193, 4348, 396535, 24238, 20352, 165213, 68718, 54186, 587, 74037, 55157, 77117, 333339, 9261, 10950, 205596, 209764, 324786, 843, 55156, 346, 150540, 526431, 4588, 605, 539, 372058, 176, 359940, 152532, 49519, 292362, 205, 598, 2503, 11471, 81, 315846, 47423, 132344, 497, 77, 39693, 31743, 265195, 45380, 872, 505192, 244786, 82690, 295279, 62, 12405, 475557, 425, 11647, 26466, 40751, 508, 508442, 15804, 89825, 7350, 16859, 13398, 44214, 475149, 16074, 901, 380, 45612, 11036, 334541, 57627, 644, 8290, 424694, 39915, 12477, 280, 548, 76341, 40213, 782, 406997, 16869, 12429, 473267, 220289, 1541, 604, 1372, 525832, 313369, 695932, 25050, 1830, 43824, 286217, 2502, 33320, 12444, 122973, 4476, 9345, 18311, 2501, 8055, 198277, 1427, 36970, 14069, 675, 7508]
    # server.common.set_cache('top250', 'douban', DouBanTop250)
    get_top250()
    _LOGGER.info(f'{plugins_name}手动获取最新 TOP250 列表完成')


@plugin.command(name='single_video', title='整理 PLEX 媒体', desc='整理指定电影名称的媒体', icon='LocalMovies', run_in_background=True)
def single_video(ctx: PluginCommandContext,
                single_videos: ArgSchema(ArgType.String, '整理指定电影名称的媒体,支持回车换行，一行一条', '', default_value='', required=True),
                spare_flag: ArgSchema(ArgType.Enum, '启用备用整理方案，默认启用', '', enum_values=lambda: spare_flag_list, default_value='on', multi_value=False, required=False)):
    spare_flag = bool(spare_flag and spare_flag.lower() != 'off')
    _LOGGER.info(f'{plugins_name}开始手动整理指定媒体')
    plexst.process_single_video(single_videos,spare_flag)
    # plexst.process_collection()
    _LOGGER.info(f'{plugins_name}手动整理指定媒体完成')



# @plugin.command(name='plexcollection', title='Plex整理合集首字母', desc='自动整理合集首字母', icon='HourglassFull',run_in_background=True)
# def echo_c(ctx: PluginCommandContext):
#     plexst.process_collections()
#     user_list = list(filter(lambda x: x.role == 1, mbot_api.user.list()))
#     if user_list:
#         for user in user_list:
#             mbot_api.notify.send_system_message(user.uid, 'Plex整理合集首字母',
#                                                 '自动整理合集首字母')
#     return PluginCommandResponse(True, f'Plex合集整理完成')

