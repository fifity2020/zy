import urllib.request, subprocess, sys, re, time, ssl, os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ================= 配置区 =================
# 1. 源地址
SOURCE_URLS = [


]

# 2. 私人频道列表 (锁定分组)
MY_PRIVATE_CHANNELS = [
   
]

# 3. 代理配置
PROXY_ADDR = "http://192.168.20.2:7890"
PROXY_DOMAINS = ["stream-link.org", "passwdword.xyz", "tv.iill.top"]

# 4. 分组排序
GROUP_ORDER = ["记录频道", "央视频道", "卫视频道", "影视频道", "音乐时尚", "国际频道", "体育频道", "其他"]

# 5. 扫描参数
LAN_IP = "192.168.*.*"
LOGO_BASE_URL = "https://epg.iill.top/logo/"
MAX_WORKERS = 5
SAVE_PATH = "/app/checked_all.m3u"
WHITE_LIST = ["CCTV", "卫视", "深圳卫视", "纪实", "翡翠台", "CGTN纪录", "BBC Earth", "Animal_Plane", "CHC", "亞洲美食頻道", "Discovery-Asia", "亚洲TLC", "tvN", "明珠", "LOVE NATURE", "亞洲旅遊", "視納華仁紀實频道", "Clarity 4K", "Loupe 4K", "凤凰卫视资讯台", "凤凰卫视中文台", "中天新闻", "TVBS新闻", "东森新闻", "重温经典", "南国都市", "美亚电影", "爱奇艺", "amc電影台", "我的歐洲電影", "TVB星河", "天映频道", "TVB Plus", "HBO", "CLASSICA", "古典乐", "電影原聲台", "MEZZO", "Fashiontv", "FASHIONBOX", "CNA", "BBC News International", "ABC News", "CNN International", "Fox News", "NHKWORLD", "CNBC"]
BLACK_LIST = ["CCTV1港澳版", "CCTV7", "CCTV12", "CCTV13", "CCTV14", "卫视中文台", "CCTV17", "大湾区卫视", "世界地理", "兵器科技", "卫生健康", "央视台球", "文化精品", "女性时尚", "电视指南", "风云足球", "风云音乐", "高尔夫网球", "三沙卫视", "云南卫视", "兵团卫视", "内蒙古卫视", "农林卫视", "厦门卫视", "唐人卫视", "宁夏卫视", "广西卫视", "新疆卫视", "河北卫视", "西藏卫视", "藏语卫视", "延边卫视", "青海卫视", "南方卫视", "四川卫视"]

# 6. 核心精选权重 (第一梯队：1-49)
# 只要命中这里，就是顶级优先，数字越小越靠前
CHANNEL_WEIGHTS = {
    "重温经典": 1, "北京卫视": 2, "湖南卫视": 3, "浙江卫视": 4, "江苏卫视": 5, "东方卫视": 6,
    "CHC": 10, "China Travel": 11, "Discovering China": 12,
    "CLASSICA": 20, "MEZZO": 21, "電影原聲台": 22,
    "Clarity 4K": 30, "Loupe 4K": 31, "BBC Earth": 32, "Animal_Plane": 33, 
    "Discovery-Asia": 34, "NATURE": 35, "亚洲TLC": 36      
}

# ================= 核心逻辑区 =================

def get_group(name):
    name_up = name.upper()
    conf = [
        (["纪实", "CGTN纪录", "BBC Earth", "Animal_Plane", "亞洲美食頻道", "Discovery-Asia", "亚洲TLC", "tvN", "明珠", "LOVE NATURE", "亞洲旅遊", "視納華仁紀實頻道", "Clarity 4K", "Loupe 4K"], "记录频道"),
        (["CCTV"], "央视频道"),
        (["卫视", "凤凰卫视资讯台", "凤凰卫视中文台", "中天新闻", "TVBS新闻", "东森新闻"], "卫视频道"),
        (["CLASSICA", "古典乐", "電影原聲台", "MEZZO", "FASHIONBOX", "Fashiontv"], "音乐时尚"),
        (["CHC", "重温经典", "南国都市", "美亚电影", "爱奇艺", "amc電影台", "我的歐洲電影", "TVB星河", "天映频道", "TVB Plus", "HBO"], "影视频道"),
        (["CNA", "BBC News International", "ABC News", "CNN International", "Fox News", "NHKWORLD", "CNBC"], "国际频道")
    ]
    for keywords, g_name in conf:
        if any(k in name_up for k in keywords): return g_name
    return "其他"

def sort_key(name):
    """
    分层排序逻辑（越小越靠前）：
    1. 精选字典命中 (1-49)
    2. 普通内地卫视 (50)
    3. 港澳台及海外频道 (80)
    4. 央视数字频道 (100+)
    5. 其他 (999)
    """
    name_up = name.upper()
    
    # 优先匹配精选字典
    for key, weight in CHANNEL_WEIGHTS.items():
        if key.upper() in name_up: return weight
    
    # 普通内地卫视（排除港澳凤凰等）
    if "卫视" in name_up and not any(k in name_up for k in ["凤凰", "翡翠", "TVB", "澳门", "香港"]):
        return 50
    
    # 港澳台及关联
    ga_keywords = ["凤凰", "翡翠", "TVB", "中天", "东森", "TVBS", "明珠", "J2", "天映", "星河", "PLUS"]
    if any(k in name_up for k in ga_keywords):
        return 80
    
    # 央视/数字
    nums = re.findall(r'\d+', name_up)
    if nums: return 100 + int(nums[0])
        
    return 999

def check_quality(task):
    url = task['url']
    try:
        test_url = url.replace("172.17.0.5", LAN_IP)
        env = os.environ.copy()
        if any(dom in url for dom in PROXY_DOMAINS):
            env["http_proxy"] = PROXY_ADDR; env["https_proxy"] = PROXY_ADDR
        cmd = ['ffmpeg', '-hide_banner', '-t', '2', '-i', test_url, '-f', 'null', '-']
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=20, env=env)
        match = re.search(r' (\d{3,4})x(\d{3,4})', proc.stderr)
        if match:
            height = int(match.group(2))
            # 只要分辨率 >= 720，就认为是合格的
            if height >= 720:
                return {"name": task['name'], "url": url, "height": height}
    except: pass
    return None

def run():
    print(f"[{time.strftime('%H:%M:%S')}] 启动阶梯排序引擎：精选 > 卫视 > 港澳...")
    pool = {}; fixed_pool = {}; seen_urls = set()
    
    # 注入私人频道
    for p in MY_PRIVATE_CHANNELS:
        raw_name = p['name'].upper().strip()
        c_n = re.sub(r'[\(\[（【「].*?[\)\]）】」]|多音轨|字幕|语音|内嵌|高清|标清|粤语|英语| ', '', raw_name)
        c_n = re.sub(r'(CCTV-?\d+).*', r'\1', c_n).replace("-", "")
        if c_n not in fixed_pool:
            fixed_pool[c_n] = {"url": p['url'], "group": p.get('group', get_group(c_n))}
        seen_urls.add(p['url'])

    # 抓取逻辑
    opener_dir = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    opener_pxy = urllib.request.build_opener(urllib.request.ProxyHandler({'http': PROXY_ADDR, 'https': PROXY_ADDR}))
    tasks = []
    for s_url in SOURCE_URLS:
        try:
            op = opener_pxy if any(d in s_url for d in PROXY_DOMAINS) else opener_dir
            with op.open(urllib.request.Request(s_url, headers={'User-Agent':'PotPlayer'}), timeout=20) as r:
                lines = r.read().decode('utf-8', errors='ignore').splitlines()
                for i in range(len(lines)):
                    if "#EXTINF" in lines[i] and i+1 < len(lines):
                        raw_name = lines[i].split(",")[-1].upper()
                        c_n = re.sub(r'[\(\[（【「].*?[\)\]）】」]|多音轨|字幕|语音|内嵌|高清|标清|粤语|英语| ', '', raw_name)
                        c_n = re.sub(r'(CCTV-?\d+).*', r'\1', c_n).replace("-", "")
                        url = lines[i+1].strip()
                        if any(b in c_n for b in BLACK_LIST): continue
                        if any(w in c_n for w in WHITE_LIST) and url not in seen_urls:
                            tasks.append({"name": c_n, "url": url})
                            seen_urls.add(url)
        except Exception as e: print(f"源错误: {e}")

    # 质检
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as exe:
        quality_tasks = [t for t in tasks if t['name'] not in fixed_pool]
        results = [f.result() for f in as_completed([exe.submit(check_quality, t) for t in quality_tasks]) if f.result()]
        
        for r in results:
            n = r['name']
            if n not in pool:
                pool[n] = {"best_url": None, "max_height": 0}
            
            # 核心逻辑：保留分辨率最高的那一个源
            if r['height'] > pool[n]['max_height']:
                pool[n]['max_height'] = r['height']
                pool[n]['best_url'] = r['url']

    # 合并写入
    all_names = set(list(fixed_pool.keys()) + list(pool.keys()))
    written_names = set()

    with open(SAVE_PATH, "w", encoding="utf-8") as f:
        f.write('#EXTM3U x-tvg-url="https://epg.iill.top/e.xml" catchup="append"\n')
        for g in GROUP_ORDER:
            chans = sorted([n for n in all_names if (fixed_pool[n]['group'] if n in fixed_pool else get_group(n)) == g and n not in written_names], key=sort_key)
            for n in chans:
                logo = f"{LOGO_BASE_URL}{n}.png".replace(" ", "%20")
                urls = [fixed_pool[n]['url']] if n in fixed_pool else [pool[n]["best_url"]]
                for u in urls:
                    f_url = u.replace("172.17.0.5", LAN_IP).replace("localhost", LAN_IP)
                    f.write(f'#EXTINF:-1 tvg-id="{n}" tvg-logo="{logo}" group-title="{g}" catchup="default" catchup-days="7",{n}\n{f_url}\n')
                    written_names.add(n)

    print(f"[{time.strftime('%H:%M:%S')}] OK! 列表已按：重温经典 > 湘浙苏京 > 省市卫视 > 港澳 的顺序生成。")

if __name__ == "__main__":
    run()
