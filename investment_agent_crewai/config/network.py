# config/network.py
# 以后你换服务器或 Docker / 云部署，只改这一个文件

import os

def setup_network():
    # 1. 设置本地代理地址 (请确保你的VPN软件确实监听在这个端口)，（给 Serper / Google 用）
    proxy_url = "http://127.0.0.1:15236"

    # 2. 启用代理 (主要为了 Serper 和其他海外 API)
    os.environ["http_proxy"] = proxy_url
    os.environ["https_proxy"] = proxy_url

    # 3. 设置不走代理白名单 (直连名单)
    # 关键修改：加入 AkShare 常用的国内财经数据源域名，强制它们不走代理
    no_proxy_list = [
        "api.deepseek.com",  # DeepSeek
        "127.0.0.1", 
        "localhost",
        "eastmoney.com",     # 东方财富 (AkShare主要源)
        "sina.com.cn",       # 新浪财经
        "163.com",           # 网易财经
        "cninfo.com.cn",     # 巨潮资讯
        "sse.com.cn",        # 上交所
        "szse.cn"            # 深交所
    ]
    
    os.environ["no_proxy"] = ",".join(no_proxy_list)

    print(f"🌐 网络环境配置完成 | 代理: {proxy_url} | 直连: DeepSeek & 国内财经源")

