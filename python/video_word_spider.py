import requests
import json
import re
import time
import base64
import sys
import os

class BilibiliSubtitleDownloader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def extract_video_id(self, url):
        """从URL中提取BV号或AV号"""
        bv_pattern = r'BV\w{10}'
        av_pattern = r'av(\d+)'
        
        bv_match = re.search(bv_pattern, url)
        if bv_match:
            return bv_match.group(0)
        
        av_match = re.search(av_pattern, url)
        if av_match:
            return f"av{av_match.group(1)}"
        
        # 如果直接输入的是BV号
        if url.startswith('BV'):
            return url
        
        raise ValueError("无法从URL中提取视频ID，请确保URL包含BV号或AV号")
    
    def get_video_info(self, video_id):
        """获取视频信息"""
        if video_id.startswith('BV'):
            api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={video_id}"
        else:  # 假设是av号
            aid = video_id.replace('av', '')
            api_url = f"https://api.bilibili.com/x/web-interface/view?aid={aid}"
        
        response = self.session.get(api_url)
        if response.status_code != 200:
            raise Exception(f"获取视频信息失败: {response.status_code}")
        
        data = response.json()
        if data['code'] != 0:
            raise Exception(f"API返回错误: {data['message']}")
        
        return data['data']
    
    def get_subtitle_list(self, video_id, cid):
        """获取视频字幕列表"""
        # 使用视频播放接口获取字幕信息
        if video_id.startswith('BV'):
            api_url = f"https://api.bilibili.com/x/player/v2?bvid={video_id}&cid={cid}"
        else:  # 假设是av号
            aid = video_id.replace('av', '')
            api_url = f"https://api.bilibili.com/x/player/v2?aid={aid}&cid={cid}"
        
        response = self.session.get(api_url)
        if response.status_code != 200:
            raise Exception(f"获取字幕列表失败: {response.status_code}")
        
        data = response.json()
        if data['code'] != 0:
            raise Exception(f"API返回错误: {data['message']}")
        
        subtitle_info = data['data'].get('subtitle', {})
        subtitles = subtitle_info.get('subtitles', [])
        
        return subtitles
    
    def get_subtitle_content(self, subtitle_url):
        """获取字幕内容"""
        # 补全URL（如果需要）
        if not subtitle_url.startswith('http'):
            subtitle_url = f"https:{subtitle_url}"
        
        response = self.session.get(subtitle_url)
        if response.status_code != 200:
            raise Exception(f"获取字幕内容失败: {response.status_code}")
        
        data = response.json()
        return data
    
    def parse_subtitle_content(self, subtitle_data):
        """解析字幕内容为文本格式"""
        result = []
        for item in subtitle_data.get('body', []):
            start_time = self.format_time(item.get('from'))
            end_time = self.format_time(item.get('to'))
            content = item.get('content', '')
            
            result.append(f"[{start_time} --> {end_time}] {content}")
        
        return result
    
    def format_time(self, seconds):
        """将秒数格式化为 时:分:秒.毫秒 格式"""
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}.{int((seconds - int(seconds)) * 1000):03d}"
    
    def get_subtitle(self, video_url, language='zh-CN'):
        """获取视频字幕并返回格式化文本"""
        try:
            # 提取视频ID
            video_id = self.extract_video_id(video_url)
            print(f"提取到视频ID: {video_id}")
            
            # 获取视频信息
            video_info = self.get_video_info(video_id)
            title = video_info.get('title', 'Unknown Title')
            cid = video_info.get('cid')
            
            if not cid:
                # 如果是多P视频，取第一P的cid
                if 'pages' in video_info and len(video_info['pages']) > 0:
                    cid = video_info['pages'][0]['cid']
                else:
                    raise Exception("无法获取视频的cid")
            
            print(f"视频标题: {title}")
            print(f"CID: {cid}")
            
            # 获取字幕列表
            subtitles = self.get_subtitle_list(video_id, cid)
            
            if not subtitles:
                print("该视频没有字幕")
                return None
            
            # 筛选指定语言的字幕
            target_subtitle = None
            for subtitle in subtitles:
                if subtitle.get('lan') == language:
                    target_subtitle = subtitle
                    break
            
            # 如果没有找到指定语言，使用第一个字幕
            if not target_subtitle and subtitles:
                target_subtitle = subtitles[0]
                print(f"未找到{language}字幕，使用{target_subtitle.get('lan')}字幕")
            
            if not target_subtitle:
                print("未找到可用字幕")
                return None
            
            # 获取字幕内容
            subtitle_url = target_subtitle.get('subtitle_url')
            subtitle_data = self.get_subtitle_content(subtitle_url)
            
            # 解析字幕内容
            parsed_subtitle = self.parse_subtitle_content(subtitle_data)
            
            return {
                'title': title,
                'video_id': video_id,
                'language': target_subtitle.get('lan'),
                'subtitle': parsed_subtitle
            }
            
        except Exception as e:
            print(f"获取字幕发生错误: {e}")
            return None

    def save_subtitle(self, subtitle_data, output_file=None):
        """保存字幕为文本文件"""
        if not subtitle_data:
            print("没有字幕数据可保存")
            return
        
        if not output_file:
            output_file = f"{subtitle_data['video_id']}_{subtitle_data['language']}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"标题: {subtitle_data['title']}\n")
            f.write(f"视频ID: {subtitle_data['video_id']}\n")
            f.write(f"语言: {subtitle_data['language']}\n\n")
            
            for line in subtitle_data['subtitle']:
                f.write(f"{line}\n")
        
        print(f"字幕已保存到: {output_file}")
        return output_file

def main():
    downloader = BilibiliSubtitleDownloader()
    
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        video_url = 'https://www.bilibili.com/video/BV16BdmYmESK/'

    language = 'zh-CN'  # 默认获取中文字幕
    if len(sys.argv) > 2:
        language = sys.argv[2]
    
    subtitle_data = downloader.get_subtitle(video_url, language)
    
    if subtitle_data:
        output_file = downloader.save_subtitle(subtitle_data)
        
        # 打印部分字幕内容预览
        print("\n字幕内容预览:")
        for i, line in enumerate(subtitle_data['subtitle']):
            print(line)
            if i >= 10:  # 只预览前10行
                print("...")
                break
    else:
        print("未能获取字幕")

if __name__ == "__main__":
    main()