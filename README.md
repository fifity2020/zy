



Tivimate4.0以上可以设置回看，
条件1:回看源
条件2:  1、直播源项目中设置回看为自动
        2、直播源在直播源文件头中把"#EXTM3U"改为#EXTM3U url-tvg="http://epg.51zmt.top:8000/e.xml" catchup="append" catchup-source="?playseek=${(b)yyyyMMddHHmmss}-${(e)yyyyMMddHHmmss}"

