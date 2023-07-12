## 新增为海报添加媒体信息
清理不需要的海报图片（当多次运行添加媒体信息后可能会有一些不需要的海报） [按此链接的方法清理](https://metamanager.wiki/en/latest/home/scripts/image-cleanup.html)

建议使用docker版，在/config 文件夹下建立环境变量配置文件 `.env`,示例如下：
```console
PLEX_PATH=/plex
MODE=remove
SCHEDULE=
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

<img width="1628" alt="image" src="https://github.com/Alano-i/Plex-Tools/assets/68833595/aaf76b61-8fba-44f6-96fe-8f0635e1b3d8">

