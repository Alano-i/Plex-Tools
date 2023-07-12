import requests
from PIL import Image, ImageDraw, ImageFilter,ImageFont,ImageEnhance
from plexapi.server import PlexServer
from io import BytesIO
import xml.etree.ElementTree as ET
import os
import time
import logging
import urllib3
from urllib3.exceptions import MaxRetryError, ConnectionError, TimeoutError
loger = logging.getLogger(__name__)
plugins_name = '「PLEX 工具箱」'

# 设置字体文件的路径（根据需要修改）
base_path = '/data/plugins/plexsortout/overlays'

def add_config(config):
    global mbot_url, mbot_api_key, plex_url, plex_token
    mbot_url = config.get('mbot_url','')
    mbot_api_key = config.get('mbot_api_key','')
    plex_url = config.get('plex_url','')
    plex_token = config.get('plex_token','')

def save_img(img_url,title,lib_name):
    overlay_flag = False
    img_dir = os.path.join(base_path, f'poster_backup/{lib_name}')
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, f"{title}.jpg")
    retries = 5
    retry_delay = 3
    for i in range(retries):
        try:
            http = urllib3.PoolManager()
            response = http.request('GET', img_url)
            with open(f"{img_dir}/tmp.jpg", "wb") as f:
                f.write(response.data)

            # 读取图片信息，EXIF标签是否是overlay
            poster = Image.open(f"{img_dir}/tmp.jpg")
            exif_tags = poster.getexif()
            if 0x04bc in exif_tags and exif_tags[0x04bc] == "overlay":
                overlay_flag = True
            if not overlay_flag:
                with open(img_path, "wb") as f:
                    f.write(response.data)
                # loger.info(f"{title} 的海报/背景已存入{img_path}")
            break
        except (ConnectionError, TimeoutError, MaxRetryError) as e:
            loger.error(f'「{title}」保存 {img_url} 到本地 {i+1}/{retries} 次请求异常，原因：{e}')
            time.sleep(retry_delay)
            img_path = ''
            continue
        except Exception as e:
            loger.error(f'「{title}」保存 {img_url} 到本地 {i+1}/{retries} 次请求异常，原因：{e}')
            img_path = ''
            continue
    return img_path,overlay_flag

# 大小单位转换，输入Bytes
def convert_bytes_to_gbm(bytes_value):
    gb = bytes_value / (1024 ** 3)  # 转换为GB
    if gb >= 1:
        return f"{gb:.2f}GB"
    else:
        mb = bytes_value / (1024 ** 2)  # 转换为MB
        return f"{mb:.2f}MB"

def convert_milliseconds(milliseconds):
    milliseconds = int(milliseconds)
    minutes = milliseconds // 60000  # 毫秒转分钟
    if minutes >= 60:
        hours = minutes // 60
        minutes %= 60
        return f"{hours}小时 {minutes}分钟"
    else:
        return f"{minutes}分钟"

def get_display_title(key):
    # plex = PlexServer(plex_url, plex_token)
    # plex_url = plex.url('')
    # plex_token = plex._token
    url = plex_url + key + '?X-Plex-Token=' + plex_token
    response = requests.get(url)
    if response.status_code == 200:
        # 解析XML
        root = ET.fromstring(response.text)
        """
        streamType="1": 视频流 (Video Stream)
        streamType="2": 音频流 (Audio Stream)
        streamType="3": 字幕流 (Subtitle Stream)
        streamType="4": 章节流 (Chapter Stream)
        """
        # 使用XPath定位第一个streamType="1"的Stream元素
        stream_element = root.find('.//Video/Media/Part/Stream[@streamType="1"]')
        # 使用XPath定位所有的streamType="1"的Stream元素
        # stream_elements = root.findall('.//Video/Media/Part/Stream[@streamType="1"]')
        if stream_element is not None:
            display_title = stream_element.get('displayTitle')
            if display_title:
                return display_title
    return ''


def new_poster(media_type,resolution,rdynamic_range,duration,rating,poster_path,title):
    try:
        rating = str(rating)
        if rating == '10.0': rating = '10'
        if media_type == 'movie':
            poster_width = 1000
            poster_height = 1500
            scale = 1215/1000
            if resolution == '1080P':
                scale = 1192/1000
                duration = duration.replace(' ','')
            if rdynamic_range =='DV':
                scale = 1180/1000
                duration = duration.replace(' ','')

        elif media_type == 'show':
            poster_width = 1000
            poster_height = 563
            scale = 700/1000
        # resolution = '4k'
        # rdynamic_range = 'HDR'
        # rdynamic_range = 'DV'
        # duration = '2小时 35分钟'
        # rating = '8.5'

        img_path = f'{base_path}/img' 

        # 打开原始海报图像
        original_image = Image.open(poster_path)
        resized_image = original_image.resize((poster_width, poster_height))

        # 创建一个与海报相同尺寸的新图像(RGBA)
        new_image = Image.new("RGBA", resized_image.size)
        new_image.paste(resized_image, (0, 0))
        # 将改变大小后的海报高斯模糊
        blurred_image = new_image.filter(ImageFilter.GaussianBlur(radius=35))

        # 创建一个与原始海报相同尺寸的透明黑色层图像
        black_alpha = 165
        black_layer = Image.new("RGBA", resized_image.size, (0, 0, 0, black_alpha))

        # 将高斯模糊后的海报上叠加黑色透明层
        poster_image = Image.alpha_composite(blurred_image, black_layer)
        try:
            # 实现黑色透明层与海报图像混合模式：正片叠底效果
            # 获取图像像素数据
            pixels = poster_image.load()
            # 迭代每个像素并应用正片叠底混合模式
            for y0 in range(poster_image.height):
                for x0 in range(poster_image.width):
                    r, g, b, a = pixels[x0, y0]
                    pixels[x0, y0] = (r * a // 255, g * a // 255, b * a // 255, a)
            # 饱和度
            enhancer = ImageEnhance.Color(poster_image)
            saturation_factor = 1.7  # 饱和度增强因子，大于1增强，小于1减弱
            enhanced_image = enhancer.enhance(saturation_factor)
            # 色阶（对比度）
            enhancer = ImageEnhance.Contrast(enhanced_image)
            contrast_factor = 1.65  # 色阶增强因子，大于1增强，小于1减弱
            poster_image = enhancer.enhance(contrast_factor)
        except Exception as e:
            loger.error(f'{plugins_name}调整色阶、饱和度、混合模式时发生错误，原因：{e}')

        # 创建海报层图像
        poster = Image.new("RGBA", (poster_width, poster_height))

        # 创建一个与海报相同尺寸的遮罩图像
        mask = Image.new("L", poster.size)

        # 在遮罩图像上绘制圆角矩形
        draw = ImageDraw.Draw(mask)
        radius = int(20 * scale)  # 圆角矩形的半径
        if media_type == 'movie':
            x = int(22 * scale)-4  # 距离左侧边缘的距离
        elif media_type == 'show':
            x = int(22 * scale)
        bottom = int(28 * scale)
        bar_height = int(110 * scale)
        y = poster.height - bottom - bar_height  # 距离底部的距离
        right = poster.width - x  # 距离右侧边缘的距离
        y0 = int(22 * scale)

        draw.rounded_rectangle([(x, y), (right, y + bar_height)], radius, fill=255)
        # 创建一个与海报相同尺寸的遮罩图像
        outline = Image.new("RGBA", poster.size)
        # 在遮罩图像上绘制圆角矩形
        draw = ImageDraw.Draw(outline)
        if media_type == 'movie':
            draw.rounded_rectangle([(x-2, y-2), (right+2, y + bar_height+2)], radius+2, fill=(255,255,255,28))
        elif media_type == 'show':
            draw.rounded_rectangle([(x-1, y-1), (right+1, y + bar_height+1)], radius+1, fill=(255,255,255,28))

        # 在新图像上叠加原始海报
        poster.paste(resized_image, (0, 0))

        # 将描边层和海报层叠加
        poster = Image.alpha_composite(poster, outline)

        # 将高斯模糊后的海报叠加到新海报，并将遮罩应用于模糊图像
        poster.paste(poster_image, (0, 0), mask=mask)

        png_height = int(62 * scale)

        # 分辨率
        resolution_png = Image.open(f"{img_path}/{resolution}.png").convert("RGBA")
        resolution_png = resolution_png.resize((int(png_height*resolution_png.width/resolution_png.height), png_height))
        # 创建一个与海报图像相同尺寸的图像
        resolution_image = Image.new("RGBA", poster.size)
        x_resolution = int(x+22 * scale)
        y_resolution = int(y+bar_height/2 - resolution_png.height/2)

        resolution_image.paste(resolution_png, (x_resolution, y_resolution))
        poster = Image.alpha_composite(poster, resolution_image)

        # 动态范围
        x_rdynamic_range = int(x_resolution + resolution_png.width + 20 * scale)

        rdynamic_range_png = Image.open(f"{img_path}/{rdynamic_range}.png").convert("RGBA")
        rdynamic_range_png = rdynamic_range_png.resize((int(png_height*rdynamic_range_png.width/rdynamic_range_png.height), png_height))
        # 创建一个与海报图像相同尺寸的图像
        rdynamic_range_image = Image.new("RGBA", poster.size)

        rdynamic_range_image.paste(rdynamic_range_png, (x_rdynamic_range, y_resolution))
        poster = Image.alpha_composite(poster, rdynamic_range_image)

        # 时长
        font_path = f'{base_path}/font/fzlth.ttf'
        font_path_n = f'{base_path}/font/ALIBABA_Bold.otf'
        draw = ImageDraw.Draw(poster)
        if rdynamic_range =='DV' and media_type == 'movie':
            font_r = ImageFont.truetype(f"{font_path}", int(51 * scale))
        else:
            font_r = ImageFont.truetype(f"{font_path}", int(54 * scale))
        font_n = ImageFont.truetype(f"{font_path_n}", int(75 * scale))

        # text_width, text_height = draw.textsize(duration, font=font_r)
        text_width = int(draw.textlength(duration, font_r))
        text_height = 52 * scale

        # text_width0, text_height0 = draw.textsize(rating, font=font_n)
        text_width0 = int(draw.textlength(rating, font_n))
        text_height0 = 52 * scale

        y_duration = int(y+bar_height/2 - text_height/2)

        if media_type == 'movie':
            x_duration = int(x_resolution + resolution_png.width + 20 * scale + rdynamic_range_png.width + 22 * scale)
        elif media_type == 'show':
            x_duration = int(x_resolution + resolution_png.width + 20 * scale + rdynamic_range_png.width + 30 * scale)

        y_n = int(y+bar_height/2 - text_height0/2)
        if media_type == 'movie':
            draw.text((x_duration, y_duration-3 * scale), duration, fill=(255,255,255,255),font=font_r)
            if rdynamic_range =='DV':
                draw.text((right-26 * scale-text_width0, y_n-23 * scale), rating, fill=(255,155,21,255),font=font_n)
            else:
                draw.text((right-30 * scale-text_width0, y_n-23 * scale), rating, fill=(255,155,21,255),font=font_n)

        elif media_type == 'show':
            draw.text((x_duration, y_duration-5 * scale+1), duration, fill=(255,255,255,255),font=font_r)
            draw.text((right-30 * scale-text_width0, y_n-23 * scale+2), rating, fill=(255,155,21,255),font=font_n)

        poster = poster.convert("RGB")
        # poster.save(f"/Users/alano/Documents/py测试/plex/new_poster4.jpg", quality=97)

        # out_path = f"{base_path}/done/{os.path.basename(poster_path)}"
        out_path = f"{base_path}/tmp.jpg"
        # poster.save(out_path, quality=97)
        # 添加自定义的EXIF标签
        exif_tags = poster.getexif()
        exif_tags[0x04bc] = "overlay"
        # 保存图像并将EXIF标签写入
        poster.save(out_path, quality=97, exif=exif_tags)

        # 读取图片信息，EXIF标签是否是overlay
        # posterddd = Image.open(out_path)
        # exif_tags = posterddd.getexif()
        # if 0x04bc in exif_tags and exif_tags[0x04bc] == "overlay":
        #     overlay_flag = True

        return out_path
    except Exception as e:
        loger.error(f'处理「{title}」时发生错误，原因：{e}')

def get_local_info(media):
    # 文件名
    try:
        file_name = os.path.basename(media.locations[0])
        # file_name = os.path.basename(media.media[0].parts[0].file)  # 此行也可获取文件名
    except Exception as e:
        file_name = ''
    # 时长
    try:
        duration = convert_milliseconds(media.duration)
    except Exception as e:
        duration = ''
    # 大小
    try:
        size = convert_bytes_to_gbm(media.media[0].parts[0].size)
    except Exception as e:
        size = ''
    # bitrate
    try:
        bitrate = f"{round(media.media[0].bitrate / 1000, 1)}Mbps"
    except Exception as e:
        bitrate = ''
    # 分辨率
    try:
        videoResolution = media.media[0].videoResolution.lower() #480 720 1080 4k
        videoResolution = videoResolution if videoResolution == '4k' else f"{videoResolution}P"
        videoResolution = videoResolution.upper()
    except Exception as e:
        videoResolution = ''
    # 动态范围
    try:
        key = media.key # /library/metadata/33653
        display_title = get_display_title(key).lower()
        # display_title = media.media[0].parts[0].streams[0].displayTitle.lower(), #'4K DoVi (HEVC Main 10) 4K HDR10 (HEVC Main 10) 1080p (H.264)
        if 'dovi' in display_title or 'dov' in display_title or 'dv' in display_title:
            display_title = 'DV'
        elif 'hdr' in display_title:
            display_title = 'HDR'
        else:
            display_title = 'SDR'
    except Exception as e:
        display_title = ''
    return file_name,duration,size,bitrate,videoResolution,display_title

def add_info_to_posters(library,lib_name,force_add):
    if library.type == 'show':
        # 获取所有剧集
        shows = library.all()
        for show in shows:
            show_year = show.year
            try:
                rating = show.audienceRating
            except Exception as e:
                rating = ''
            i=1
            for episode in show.episodes():
                for v in range(5):
                    try:
                        # if i>1:
                        #     break
                        # posters = episode.posters()
                        poster_url = episode.posterUrl
                        e = str(episode.episodeNumber).zfill(2)
                        s = str(episode.parentIndex).zfill(2)
                        t = episode.grandparentTitle
                        episode_title = f"{t} {show_year} S{s}E{e}"
                        loger.info(f"{plugins_name}开始处理['{episode_title}']")
                        img_path,overlay_flag = save_img(poster_url,episode_title,lib_name)
                        # 上传海报
                        if not overlay_flag or force_add:
                            file_name,duration,size,bitrate,videoResolution,display_title = get_local_info(episode)
                            out_path = new_poster('show',videoResolution,display_title,duration,rating,img_path,t)
                            episode.uploadPoster(filepath=out_path)
                        else:
                            loger.warning(f"['{episode_title}'] 已经处理过了，跳过")
                        break
                    except Exception as e:
                        loger.error(f"{plugins_name}第 {v+1}/5 次处理 ['{episode_title}'] 时失败，原因：{e}")
                i=i+1
        loger.info(f"{plugins_name}剧集海报添加媒体信息完成")
    elif library.type == 'movie':
        movies = library.all()
        if movies:
            movies_n = len(movies)
            i=1
            for movie in movies:
                for v in range(5):
                    try:
                        # if i>30:
                        #     break
                        try:
                            rating = movie.audienceRating
                        except Exception as e:
                            rating = ''
                        poster_url = movie.posterUrl
                        movie_title = f"{movie.title} ({movie.year})" 
                        loger.info(f"{plugins_name}开始处理 {i}/{movies_n} ['{movie_title}']")
                        img_path,overlay_flag = save_img(poster_url,movie_title,lib_name)
                        # loger.warning(f"videoResolution:{videoResolution}")
                        # loger.warning(f"display_title:{display_title}")
                        # loger.warning(f"duration:{duration}")
                        # loger.warning(f"rating:{rating}")
                        # 上传海报
                        if not overlay_flag or force_add:
                            file_name,duration,size,bitrate,videoResolution,display_title = get_local_info(movie)
                            out_path = new_poster('movie',videoResolution,display_title,duration,rating,img_path,movie_title)
                            movie.uploadPoster(filepath=out_path)
                        else:
                            loger.warning(f"['{movie_title}'] 已经处理过了，跳过")
                        break
                    except Exception as e:
                        loger.error(f"{plugins_name}第 {v+1}/5 次处理 ['{movie_title}'] 时失败，原因：{e}")
                i=i+1
        loger.info(f"{plugins_name}电影海报添加媒体信息完成")

def add_info_to_posters_main(lib_name,force_add):
    try:
        plex = PlexServer(plex_url, plex_token) 
    except Exception as e:
        loger.error(f"{plugins_name}连接 Plex 服务器失败,原因：{e}")
    try:
        library = plex.library.section(lib_name)
        add_info_to_posters(library,lib_name,force_add)
    except Exception as e:
        loger.error(f"{plugins_name}海报添加信息出现错误! 原因：{e}")

