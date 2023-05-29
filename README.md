



Tivimate4.0以上可以设置回看，条件1，必须是回看源
条件2，软件4.0以上版本，
具体设置：1、软件中直播源项目中设置回看为自动。还可以设置回看天数，
2、直播源在直播源文件头中把"#EXTM3U"改为#EXTM3U url-tvg="http://epg.51zmt.top:8000/e.xml" catchup="append" catchup-source="?playseek=${(b)yyyyMMddHHmmss}-${(e)yyyyMMddHHmmss}"
再把直播源到入到软件中就可以了。
