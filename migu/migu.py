from flask import Flask, Response, jsonify
import requests

app = Flask(__name__)

@app.route('/sports.m3u')
def get_sports():
    url = "http://192.168.20.2:1234"
    # 白名单：只保留赛事直播类
    KEYWORDS = ["体育", "CCTV5", "NBA", "足球", "赛事", "英超", "西甲", "德甲", "回放"]
    # 黑名单：彻底屏蔽你不要的频道
    BLACKLIST = [
        "购物", "测试", "暂留", "格斗", "台球", "斯诺克",
        "四海钓鱼", "陕西体育休闲频道", "武术世界", "快乐垂钓",
        "体育休闲频道", "体坛名栏汇", "赛事最经典", "辽宁广播电视台"
    ]
    
    try:
        r = requests.get(url, timeout=10)
        r.encoding = 'utf-8'
        lines = r.text.splitlines()
        output = ["#EXTM3U"]
        
        for i in range(len(lines)):
            line = lines[i].strip()
            if line.startswith("#EXTINF"):
                is_white = any(k in line for k in KEYWORDS)
                is_black = any(b in line for b in BLACKLIST)
                
                if is_white and not is_black:
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line.startswith("http"):
                            link = next_line.replace("127.0.0.1:1234", "192.168.20.2:1234").replace("migu-video:1234", "192.168.20.2:1234")
                            conn = "&" if "?" in link else "?"
                            output.append(line)
                            output.append(f"{link}{conn}mrateType=7&isH265=1")
                            break
        return Response("\n".join(output), mimetype='text/plain')
    except Exception as e:
        return str(e), 500

@app.route('/sports.json')
def get_sports_json():
    # 和 m3u 保持完全一致的配置
    url = "http://192.168.20.2:1234"
    KEYWORDS = ["体育", "CCTV5", "NBA", "足球", "赛事", "英超", "西甲", "德甲", "回放"]
    BLACKLIST = [
        "购物", "测试", "暂留", "格斗", "台球", "斯诺克",
        "四海钓鱼", "陕西体育休闲频道", "武术世界", "快乐垂钓",
        "体育休闲频道", "体坛名栏汇", "赛事最经典", "辽宁广播电视台"
    ]
    
    try:
        r = requests.get(url, timeout=10)
        r.encoding = 'utf-8'
        lines = r.text.splitlines()
        channels = []
        
        for i in range(len(lines)):
            line = lines[i].strip()
            if line.startswith("#EXTINF"):
                is_white = any(k in line for k in KEYWORDS)
                is_black = any(b in line for b in BLACKLIST)
                
                if is_white and not is_black:
                    name = line.split(",", 1)[-1].strip()
                    # 找 URL（和 m3u 逻辑完全一样）
                    for j in range(i + 1, min(i + 5, len(lines))):
                        next_line = lines[j].strip()
                        if next_line.startswith("http"):
                            link = next_line.replace("127.0.0.1:1234", "192.168.20.2:1234").replace("migu-video:1234", "192.168.20.2:1234")
                            conn = "&" if "?" in link else "?"
                            final_url = f"{link}{conn}mrateType=7&isH265=1"
                            channels.append({
                                "name": name,
                                "url": final_url
                            })
                            break
        
        # TVBox 标准格式
        return jsonify({
            "live": channels
        })
    except Exception as e:
        return jsonify({"live": []})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
