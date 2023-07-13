# 🌎 PLEX 工具箱
MR插件，PLEX 工具箱，主要功能如下图所示：

<div align=center><img src="https://github.com/Alano-i/Plex-Tools/assets/68833595/b4d3ea32-ef97-435a-a8c5-8a0723cea8d2" width="852" /></div>

## 使用说明
- 将 `plexsortout` 文件夹放到 `Plugins` 文件夹，配置好各项设置。
- 添加海报信息功能中，恢复模式仅在成功处理过的媒体上才能生效！

## 为海报添加媒体信息

<img width="1628" alt="image" src="https://github.com/Alano-i/Plex-Tools/assets/68833595/aaf76b61-8fba-44f6-96fe-8f0635e1b3d8">

### 清理不需要的海报图片
当多次运行添加媒体信息后可能会有一些不需要的海报， [按此项目的方法清理](https://github.com/meisnate12/Plex-Image-Cleanup)

建议使用docker版，Docker Compose 文件示例：
```console
version: "2.1"
services:
  plex-image-cleanup:
    image: meisnate12/plex-image-cleanup
    container_name: plex-image-cleanup
    environment:
      - TZ=TIMEZONE #optional
    volumes:
      - /path/to/config:/config
      - /path/to/plex:/plex
    restart: unless-stopped
```

安装好之后，在/config 文件夹下建立环境变量配置文件 `.env`,示例如下：
```console
PLEX_PATH=/plex
MODE=remove
SCHEDULE="05:15|daily"
PLEX_URL=http://10.0.0.1:32400
PLEX_TOKEN=12345678
DISCORD=
TIMEOUT=600
SLEEP=60
IGNORE_RUNNING=True
LOCAL_DB=False
USE_EXISTING=False
PHOTO_TRANSCODER=True
EMPTY_TRASH=True
CLEAN_BUNDLES=True
OPTIMIZE_DB=True
TRACE=True
LOG_REQUESTS=True
```


