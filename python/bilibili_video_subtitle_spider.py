import requests
import json
import re
import sys
import os
from urllib.parse import urlparse, parse_qs

# 尝试导入Cookie管理模块
try:
    from bilibili_cookie_manager import get_cookie
    HAS_COOKIE_MANAGER = True
except ImportError:
    HAS_COOKIE_MANAGER = False
    print("警告: 未找到Cookie管理模块，将尝试不使用Cookie进行请求")

def get_headers():
    """生成请求头"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.bilibili.com/',
        'Origin': 'https://www.bilibili.com'
    }
    
    # 添加Cookie
    if HAS_COOKIE_MANAGER:
        cookie_dict = get_cookie()
        if cookie_dict:
            cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
            headers['Cookie'] = cookie_str
    
    return headers

def extract_video_id(url):
    """从URL中提取视频ID (BV号或AV号)"""
    # 处理普通URL
    if 'bilibili.com/video/' in url:
        # 从URL路径中提取
        match_bv = re.search(r'bilibili\.com/video/(BV\w+)', url)
        match_av = re.search(r'bilibili\.com/video/av(\d+)', url)
        
        if match_bv:
            return match_bv.group(1)
        elif match_av:
            return f"av{match_av.group(1)}"
    
    # 处理短链接或其他格式
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    # 检查是否有bvid或aid在查询参数中
    if 'bvid' in query_params:
        return query_params['bvid'][0]
    elif 'aid' in query_params:
        return f"av{query_params['aid'][0]}"
    
    # 直接解析输入的ID
    if url.lower().startswith('av') or url.upper().startswith('BV'):
        return url
    
    raise ValueError("无法从URL中提取视频ID")

def get_video_info(video_id):
    """获取视频信息，包括aid、cid和标题"""
    headers = get_headers()
    
    if video_id.lower().startswith('av'):
        # 处理AV号
        aid = video_id[2:]
        url = f"https://api.bilibili.com/x/player/pagelist?aid={aid}"
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data['code'] != 0:
                print(f"API返回错误: {data['message']}")
                return None
            
            if not data['data']:
                print("未找到视频分P信息")
                return None
                
            cid = data['data'][0]['cid']
            title = data['data'][0].get('part', '未知标题')
            
            return {
                'aid': aid,
                'cid': cid,
                'title': title,
                'pages': data['data']
            }
            
        except Exception as e:
            print(f"获取视频信息时出错: {e}")
            return None
            
    else:
        # 处理BV号
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={video_id}"
        
        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            
            if data['code'] != 0:
                print(f"API返回错误: {data['message']}")
                return None
                
            aid = data['data']['aid']
            cid = data['data']['cid']
            title = data['data']['title']
            pages = data['data']['pages']
            
            return {
                'aid': aid,
                'cid': cid,
                'title': title,
                'pages': pages
            }
            
        except Exception as e:
            print(f"获取视频信息时出错: {e}")
            return None

def get_subtitle_list(aid, cid):
    """获取字幕列表"""
    url = f"https://api.bilibili.com/x/player/v2?aid={aid}&cid={cid}"
    headers = get_headers()
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data['code'] != 0:
            print(f"获取字幕列表失败: {data['message']}")
            return []
        
        # 提取字幕列表
        subtitle_info = data['data']['subtitle']
        subtitles = subtitle_info.get('subtitles', [])
        
        return subtitles
        
    except Exception as e:
        print(f"获取字幕列表时出错: {e}")
        return []

def get_ai_subtitle_url(aid, cid):
    """获取AI自动生成字幕的URL"""
    url = f"https://api.bilibili.com/x/player/v2?aid={aid}&cid={cid}"
    headers = get_headers()
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if data['code'] != 0:
            print(f"获取AI字幕URL失败: {data['message']}")
            return None
            
        # AI字幕通常在subtitle_url字段中，如果为空则需要使用另一个接口
        ai_subtitle_url = f"https://api.bilibili.com/x/player/v2/ai/subtitle?aid={aid}&cid={cid}"
        return ai_subtitle_url
        
    except Exception as e:
        print(f"获取AI字幕URL时出错: {e}")
        return None

def get_subtitle_content(subtitle_url, aid=None, cid=None, is_ai_subtitle=False):
    """获取字幕内容"""
    # 处理AI自动生成字幕
    if is_ai_subtitle and aid and cid:
        subtitle_url = get_ai_subtitle_url(aid, cid)
        if not subtitle_url:
            print("无法获取AI字幕URL")
            return None
            
    # 调试打印原始URL
    print(f"原始字幕URL: {subtitle_url}")
    
    # 检查URL是否为空或格式异常
    if not subtitle_url or subtitle_url == "":
        print("错误: 字幕URL为空")
        return None
        
    # 确保URL格式正确
    if not subtitle_url.startswith('http'):
        # 检查是否只有协议前缀
        if subtitle_url == 'https:' or subtitle_url == 'http:':
            print(f"错误: 字幕URL格式异常 - {subtitle_url}")
            return None
        # 补全URL
        subtitle_url = f"https:{subtitle_url}"
    
    # 打印最终请求的URL
    print(f"请求字幕URL: {subtitle_url}")
    
    headers = get_headers()
    
    try:
        response = requests.get(subtitle_url, headers=headers)
        
        # 打印调试信息
        print(f"字幕URL状态码: {response.status_code}")
        if response.status_code == 200 and response.text:
            print(f"字幕URL响应内容前50个字符: {response.text[:50]}")
        else:
            print(f"响应内容为空或请求失败")
        
        # 解析JSON
        data = response.json()
        return data
        
    except json.JSONDecodeError as e:
        print(f"解析字幕内容失败 - JSON错误: {e}")
        print(f"响应内容: {response.text}")
        return None
    except Exception as e:
        print(f"获取字幕内容时出错: {e}")
        return None

def format_time(seconds):
    """将秒数格式化为时:分:秒.毫秒格式"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"

def save_as_srt(subtitle_data, output_file):
    """将字幕保存为SRT格式"""
    if not subtitle_data or 'body' not in subtitle_data:
        print("字幕数据无效或为空")
        return False
        
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, item in enumerate(subtitle_data['body'], 1):
                start_time = format_time(item['from'])
                end_time = format_time(item['to'])
                content = item['content']
                
                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{content}\n\n")
        return True
    except Exception as e:
        print(f"保存字幕文件时出错: {e}")
        return False

def main():
    """主函数"""
    # 获取视频URL
    video_url = 'https://www.bilibili.com/video/BV11i4y1L7QQ/'
    
    try:
        # 提取视频ID
        video_id = extract_video_id(video_url)
        print(f"视频ID: {video_id}")
        
        # 获取视频信息
        video_info = get_video_info(video_id)
        if not video_info:
            print("获取视频信息失败")
            return
            
        print(f"视频标题: {video_info['title']}")
        print(f"AID: {video_info['aid']}, CID: {video_info['cid']}")
        
        # 获取字幕列表
        subtitle_list = get_subtitle_list(video_info['aid'], video_info['cid'])
        
        if not subtitle_list:
            print("该视频没有字幕")
            return
        
        print(f"找到 {len(subtitle_list)} 个字幕:")
        for i, subtitle in enumerate(subtitle_list):
            lang = subtitle.get('lan_doc', subtitle.get('lan', '未知语言'))
            print(f"{i+1}. {lang}")
        
        # 如果有多个字幕，让用户选择
        choice = 0
        if len(subtitle_list) > 1:
            try:
                choice = int(input(f"请选择要下载的字幕 (1-{len(subtitle_list)}): ")) - 1
                if choice < 0 or choice >= len(subtitle_list):
                    print("选择无效，使用第一个字幕")
                    choice = 0
            except ValueError:
                print("输入无效，使用第一个字幕")
                choice = 0
        
        selected_subtitle = subtitle_list[choice]
        lang = selected_subtitle.get('lan_doc', selected_subtitle.get('lan', '未知语言'))
        print(f"正在下载: {lang}")

        # 打印完整的字幕信息以便调试
        print(f"字幕详细信息: {json.dumps(selected_subtitle, ensure_ascii=False, indent=2)}")

        # 检查是否为AI自动生成字幕
        is_ai_subtitle = selected_subtitle.get('lan', '').startswith('ai-') or selected_subtitle.get('ai_type', 0) > 0 or not selected_subtitle.get('subtitle_url')
        
        # 获取字幕内容
        subtitle_content = get_subtitle_content(
            selected_subtitle.get('subtitle_url', ''), 
            aid=video_info['aid'], 
            cid=video_info['cid'],
            is_ai_subtitle=is_ai_subtitle
        )
        
        if not subtitle_content:
            print("获取字幕内容失败")
            return
        
        # 保存为SRT格式
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", video_info['title'])
        output_file = f"{safe_title}_{lang}.srt"
        
        if save_as_srt(subtitle_content, output_file):
            print(f"字幕已保存到: {output_file}")
        else:
            print("保存字幕文件失败")
        
    except Exception as e:
        print(f"处理过程中出错: {e}")

if __name__ == "__main__":
    main()