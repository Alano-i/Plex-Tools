import requests
from lxml import etree
import random
import re
import requests
import time
from time import sleep
from mbot.openapi import mbot_api
from mbot.core.plugins import plugin
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

_LOGGER = logging.getLogger(__name__)
plugins_name = '「PLEX 工具箱」'
server = mbot_api
session = requests.Session()
retry = Retry(connect=3, backoff_factor=0.5)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.50'}
tmdb_api_key = ''

@plugin.task('get_top250', '「更新 TOP250 列表」', cron_expression='30 8 * * *')
def task():
    _LOGGER.info(f'{plugins_name}定时任务启动，开始获取最新 TOP250 列表')
    get_top250()
    _LOGGER.info(f'{plugins_name}定时获取最新 TOP250 列表完成')
    
def get_top250_config(config):
    global tmdb_api_key
    if config.get('tmdb_api_key'):
        _LOGGER.info(f'{plugins_name}已设置 TMDB API KEY')
        tmdb_api_key = config.get('tmdb_api_key')
    else:
        _LOGGER.info(f'{plugins_name}未设置 TMDB API KEY，请先设置')
        
def get_douban_top250_cn_name():
    url = 'https://movie.douban.com/top250'
    response = session.request("GET", url, headers=headers, timeout=30)  
    html = etree.HTML(response.text)
    old_douban_top250_list = server.common.get_cache('top250', 'douban') or []
    # _LOGGER.info(f'{plugins_name}「豆瓣TOP250」列表已有缓存，共 {len(old_douban_top250_list)} 部电影，如下：\n{old_douban_top250_list}')
    # movies = {}  如果想要 movies = {1: '肖申克的救赎', 2: '霸王别姬', 3: '阿甘正传'}
    movies = []         #  movies = ['肖申克的救赎', '霸王别姬', '阿甘正传']
    for start in range(0, 250, 25):
        page_url = f'{url}?start={start}'
        response = session.request("GET", page_url, headers=headers, timeout=30)

        if response.status_code == 200:
            html = etree.HTML(response.text)
            for i in range(1, 26):
                xpath_str = f'//*[@id="content"]/div/div[1]/ol/li[{i}]/div/div[2]/div[1]/a/span[1]/text()'
                title = html.xpath(xpath_str)[0]
                movies.append(title)         # movies = ['肖申克的救赎', '霸王别姬', '阿甘正传']
                # movies[start + i] = title  # movies = {1: '肖申克的救赎', 2: '霸王别姬', 3: '阿甘正传'}
        else:
            _LOGGER.error(f'{plugins_name}请求豆瓣 TOP250 失败：{response.text}')
    if movies:
        if old_douban_top250_list != movies:
            server.common.set_cache('top250', 'douban', movies)
            new_douban_top250_list = server.common.get_cache('top250', 'douban') or []
            _LOGGER.info(f'{plugins_name}最新「豆瓣TOP250」列表已存入缓存，共 {len(movies)} 部电影，如下：\n{new_douban_top250_list}')
        else:
            _LOGGER.info(f'{plugins_name}最新「豆瓣TOP250」列表与缓存相同，共 {len(movies)} 部电影，如下：\n{movies}')
    else:
        _LOGGER.error(f'{plugins_name}获取「豆瓣TOP250」列表失败')

def get_douban_top250():
    url = 'https://movie.douban.com/top250'
    response = session.request("GET", url, headers=headers, timeout=30)  
    html = etree.HTML(response.text)
    movies = []
    for start in range(0, 250, 25):
        page_url = f'{url}?start={start}'
        response = session.request("GET", page_url, headers=headers, timeout=30)
        if response.status_code == 200:
            html = etree.HTML(response.text)
            for i in range(1, 26):
                title_xpath = f'//*[@id="content"]/div/div[1]/ol/li[{i}]/div/div[2]/div[1]/a/span[1]/text()'
                year_xpath = f'//*[@id="content"]/div/div[1]/ol/li[{i}]/div/div[2]/div[2]/p/text()'
                year_info = html.xpath(year_xpath)[1].strip()
                title = html.xpath(title_xpath)[0]
                match = re.search(r'\d{4}', year_info)
                if match:
                    year = match.group(0)
                else:
                    year = ''
                movies.append({'title': title, 'year': int(year)})
        else:
            _LOGGER.error(f'{plugins_name}请求豆瓣 TOP250 失败：{response.text}')
    return movies

# 根据豆瓣电影名称和发行年份，在TMDB API中进行查询
def tmdb_search_movie(title, year):
    API_URL = 'https://api.themoviedb.org/3'
    for j in range(5):
        try:
            response = requests.get(
                f'{API_URL}/search/movie',
                params={
                    'api_key': tmdb_api_key,
                    'query': title,
                    'year': year,
                    'with_genres': '18' # 限制搜索结果只包含电影类型的影片
                }
            )
            break
        except Exception as e:
            _LOGGER.error(f"{plugins_name} 第 {j+1} 次获取 ['{title}'] 的 tmdb_id 失败，原因：{e}")
            continue
    if response.status_code != 200:
        return None
    results = response.json().get('results')
    if not results:
        return None
    # 如果存在多个结果，则返回第一个结果
    return results[0]

def get_douban_top250_tmdb_list():
    douban_top250 = get_douban_top250()
    old_douban_top250_list = server.common.get_cache('top250', 'douban') or []
    # 根据豆瓣Top 250电影列表，建立电影名称和TMDB ID之间的对应关系
    douban_top250_tmdb_list = []
    for movie in douban_top250:
        title = movie['title']
        year = movie['year']
        result = tmdb_search_movie(title, year)
        if result:
            douban_top250_tmdb_list.append(result['id'])
        else:
            _LOGGER.error(f"{plugins_name}获取{movie} tmdb_id 失败")

    if douban_top250_tmdb_list:
        if old_douban_top250_list != douban_top250_tmdb_list:
            server.common.set_cache('top250', 'douban', movies)
            new_douban_top250_list = server.common.get_cache('top250', 'douban') or []
            _LOGGER.info(f'{plugins_name}最新「豆瓣TOP250」列表已存入缓存，共 {len(douban_top250_tmdb_list)} 部电影，如下：\n{new_douban_top250_list}')
        else:
            _LOGGER.info(f'{plugins_name}最新「豆瓣TOP250」列表与缓存相同，共 {len(douban_top250_tmdb_list)} 部电影，如下：\n{douban_top250_tmdb_list}')
    else:
        _LOGGER.error(f'{plugins_name}获取「豆瓣TOP250对应的 tmdb id」列表失败')

# 通过 IMDb ID 获取 TMDb ID
def get_tmdb_id(imdb_id, api_key):
    find_url = f'https://api.themoviedb.org/3/find/{imdb_id}?api_key={api_key}&external_source=imdb_id'
    find_response = session.request("GET", find_url, headers=headers, timeout=30)
    tmdb_id = ''
    if find_response.status_code == 200:
        find_data = find_response.json()
        tmdb_id = find_data['movie_results'][0]['id']
    else:
        _LOGGER.error(f'{plugins_name}通过 IMDb ID 获取 TMDb ID 失败')
    return tmdb_id

# 通过 TMDb ID 获取电影中文名
def get_chinese_name(imdb_id):
    api_key = tmdb_api_key
    tmdb_id = get_tmdb_id(imdb_id, api_key)
    title_url = f'https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&language=zh-CN'
    title_response = session.request("GET", title_url, headers=headers, timeout=30)

    if title_response.status_code == 200:
        title_data = title_response.json()
        chinese_title = title_data['title']
        chinese_title = chinese_title.replace('Top Gun: Maverick', '壮志凌云2：独行侠')
        chinese_title = chinese_title.replace('Spider-Man: No Way Home', '蜘蛛侠：英雄无归')
        return chinese_title
    else:
        return imdb_id
        _LOGGER.error(f'{plugins_name}通过 TMDb ID 获取电影中文名失败')

def get_imdb_top_250():
    if not tmdb_api_key:
        _LOGGER.info(f'{plugins_name}未设置 TMDB API KEY，请先设置')
        return
    old_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
    # _LOGGER.info(f'{plugins_name}「IMDB TOP250」列表已有缓存，共 {len(old_imdb_top250_list)} 部电影，如下：\n{old_imdb_top250_list}')
    url = 'https://www.imdb.com/chart/top'
    response = session.request("GET", url, headers=headers, timeout=30)
    if response.status_code == 200:
        html = etree.HTML(response.text)
        # 获取 imdbtop250 电影 imdb id
        imdb_ids = html.xpath('//td[@class="titleColumn"]/a/@href')
        imdb_ids = [id.split('/')[2] for id in imdb_ids]
        # _LOGGER.info(f'imdb_ids:{imdb_ids}')

    if imdb_ids:
        if old_imdb_top250_list != imdb_ids:
            server.common.set_cache('top250', 'imdb', imdb_ids)
            new_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
            _LOGGER.info(f'{plugins_name}最新「IMDB TOP250」列表已存入缓存，共 {len(imdb_ids)} 部电影，如下：\n{new_imdb_top250_list}')
        else:
            _LOGGER.info(f'{plugins_name}最新「IMDB TOP250」列表与缓存相同，共 {len(imdb_ids)} 部电影，如下：\n{imdb_ids}')
    else:
        _LOGGER.error(f'{plugins_name}获取「IMDB TOP250」列表失败')

    #     imdb_top250_chinese_name = []
    #     for imdb_id in imdb_ids:
    #         try:
    #             chinese_name = get_chinese_name(imdb_id)
    #             imdb_top250_chinese_name.append(chinese_name)
    #         except Exception as e:
    #             _LOGGER.error(f"{plugins_name} 获取影片中文名失败，请检查网络，原因：{e}")
    #             break
    #     #    _LOGGER.info(imdb_top250_chinese_name)
    # else:
    #     _LOGGER.error(f'{plugins_name}获取 IMDB TOP250 电影的 TMDb ID 失败')

    # if imdb_top250_chinese_name:
    #     if old_imdb_top250_list != imdb_top250_chinese_name:
    #         server.common.set_cache('top250', 'imdb', imdb_top250_chinese_name)
    #         new_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
    #         _LOGGER.info(f'{plugins_name}最新「IMDB TOP250」列表已存入缓存，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{new_imdb_top250_list}')
    #     else:
    #         _LOGGER.info(f'{plugins_name}最新「IMDB TOP250」列表与缓存相同，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{imdb_top250_chinese_name}')
    # else:
    #     _LOGGER.error(f'{plugins_name}获取「IMDB TOP250」列表失败')

def get_imdb_top_250_cn_name():
    if not tmdb_api_key:
        _LOGGER.info(f'{plugins_name}未设置 TMDB API KEY，请先设置')
        return
    old_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
    # _LOGGER.info(f'{plugins_name}「IMDB TOP250」列表已有缓存，共 {len(old_imdb_top250_list)} 部电影，如下：\n{old_imdb_top250_list}')
    url = 'https://www.imdb.com/chart/top'
    response = session.request("GET", url, headers=headers, timeout=30)
    if response.status_code == 200:
        html = etree.HTML(response.text)
        # 获取 imdbtop250 电影 imdb id
        imdb_ids = html.xpath('//td[@class="titleColumn"]/a/@href')
        imdb_ids = [id.split('/')[2] for id in imdb_ids]
        # _LOGGER.info(f'imdb_ids:{imdb_ids}')
        imdb_top250_chinese_name = []
        for imdb_id in imdb_ids:
            try:
                chinese_name = get_chinese_name(imdb_id)
                imdb_top250_chinese_name.append(chinese_name)
            except Exception as e:
                _LOGGER.error(f"{plugins_name} 获取影片中文名失败，请检查网络，原因：{e}")
                break
        #    _LOGGER.info(imdb_top250_chinese_name)
    else:
        _LOGGER.error(f'{plugins_name}获取 IMDB TOP250 电影的 TMDb ID 失败')

    if imdb_top250_chinese_name:
        if old_imdb_top250_list != imdb_top250_chinese_name:
            server.common.set_cache('top250', 'imdb', imdb_top250_chinese_name)
            new_imdb_top250_list = server.common.get_cache('top250', 'imdb') or []
            _LOGGER.info(f'{plugins_name}最新「IMDB TOP250」列表已存入缓存，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{new_imdb_top250_list}')
        else:
            _LOGGER.info(f'{plugins_name}最新「IMDB TOP250」列表与缓存相同，共 {len(imdb_top250_chinese_name)} 部电影，如下：\n{imdb_top250_chinese_name}')
    else:
        _LOGGER.error(f'{plugins_name}获取「IMDB TOP250」列表失败')

def get_top250():
    get_douban_top250_tmdb_list()
    get_imdb_top_250()
