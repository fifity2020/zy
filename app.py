from flask import Flask, Response
import requests

app = Flask(__name__)

@app.route('/sports.m3u')
def get_sports():
    url = "http://192.168.20.2:1234"
    # 白名单：你想看的
    KEYWORDS = ["体育", "CCTV5", "NBA", "足球", "赛事", "英超", "西甲", "德甲"]
    # 黑名单：你绝对不想看的（即使命中了白名单也会被剔除）
    BLACKLIST = ["购物", "测试", "暂留"]
    
    try:
        r = requests.get(url, timeout=10)
        r.encoding = 'utf-8'
        lines = r.text.splitlines()
        output = ["#EXTM3U"]
        
        for i in range(len(lines)):
            line = lines[i].strip()
            # 逻辑：必须包含白名单关键词，且不能包含黑名单关键词
            if line.startswith("#EXTINF"):
                is_white = any(k in line for k in KEYWORDS)
                is_black = any(b in line for b in BLACKLIST)
                
                if is_white and not is_black:
                    # 寻找紧随其后的 URL 行
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
