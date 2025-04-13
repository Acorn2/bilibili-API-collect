"""
B站UP主合集视频数据抓取工具
============================

本工具用于抓取B站UP主特定合集下的所有视频数据信息。

功能：
1. 支持获取UP主的所有合集列表
2. 可抓取特定合集（视频合集/视频系列）下的所有视频信息
3. 获取视频的详细信息（标题、播放量、点赞、投币等数据）
4. 将数据保存为JSON格式方便后续分析

合集类型说明：
- season: B站的"视频合集"，是UP主整理的一组相关视频的集合
- series: B站的"视频系列"，是另一种组织视频的方式

使用方法：
1. 输入UP主的mid
2. 选择是否直接输入合集ID，或从UP主的合集列表中选择
3. 抓取所有视频数据并保存到json文件

作者：[您的名字]
日期：[创建日期]
版本：1.0
"""

import requests
import time
import json
import random
import hashlib
import hmac
import re
import os
# 引入 bilibili_cookie_manager 模块
from bilibili_cookie_manager import get_cookie, get_headers

# 获取UP主的所有合集信息
def get_up_collections(mid, cookie_dict=None):
    url = "https://api.bilibili.com/x/polymer/web-space/seasons_series_list"
    params = {
        "mid": mid,
        "page_num": 1,
        "page_size": 20
    }
    
    response = controlled_request(url, params, cookie_dict=cookie_dict)
    
    if response is None:
        print("获取UP主合集信息失败")
        return []
        
    try:
        data = response.json()
        if data['code'] != 0:
            print(f"获取UP主合集信息失败，状态码：{data['code']}")
            return []
            
        # 提取合集信息
        collections = []
        
        # 添加视频合集（季）
        if 'seasons_list' in data['data']:
            for season in data['data']['seasons_list']['seasons_list']:
                collections.append({
                    'id': season['id'],
                    'title': season['title'],
                    'type': 'season',
                    'count': season['media_count']
                })
                
        # 添加视频系列
        if 'series_list' in data['data']:
            for series in data['data']['series_list']['series_list']:
                collections.append({
                    'id': series['id'],
                    'title': series['title'],
                    'type': 'series',
                    'count': series['media_count']
                })
                
        return collections
    except Exception as e:
        print(f"处理UP主合集数据时出错：{str(e)}")
        return []

# 获取合集中的所有视频
def get_collection_videos(mid, collection_id, collection_type, cookie_dict=None):
    if collection_type == 'season':
        url = "https://api.bilibili.com/x/polymer/web-space/seasons_archives_list"
        params = {
            "mid": mid,
            "season_id": collection_id,
            "page_num": 1,
            "page_size": 100  # 设置较大的值一次获取更多视频
        }
    else:  # series
        url = "https://api.bilibili.com/x/series/archives"
        params = {
            "mid": mid,
            "series_id": collection_id,
            "pn": 1,
            "ps": 100
        }
    
    response = controlled_request(url, params, cookie_dict=cookie_dict)
    
    if response is None:
        print(f"获取合集视频列表失败")
        return []
        
    try:
        data = response.json()
        if data['code'] != 0:
            print(f"获取合集视频列表失败，状态码：{data['code']}")
            return []
            
        # 提取视频信息
        if collection_type == 'season':
            videos = data['data']['archives']
        else:  # series
            videos = data['data']['archives']
            
        print(f"成功获取合集视频，共{len(videos)}个视频")
        return videos
    except Exception as e:
        print(f"处理合集视频数据时出错：{str(e)}")
        return []

# 获取单个视频的详细信息
def get_video_detail(bvid=None, aid=None, cookie_dict=None):
    params = {}
    if bvid:
        params['bvid'] = bvid
    elif aid:
        params['aid'] = aid
    else:
        return None
        
    url = "https://api.bilibili.com/x/web-interface/view"
    headers = get_headers(cookie_dict)
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"获取视频详情失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"获取视频详情出错: {str(e)}")
        return None

# 主函数
def main(mid, collection_id=None, collection_type=None, cookie_dict=None):
    # 创建data目录
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"创建data目录: {data_dir}")
    
    # 如果没有指定合集ID，则获取UP主所有合集并选择
    if not collection_id or not collection_type:
        collections = get_up_collections(mid, cookie_dict=cookie_dict)
        if not collections:
            print(f"未找到UP主 {mid} 的任何合集")
            return
            
        print(f"UP主 {mid} 共有 {len(collections)} 个合集:")
        for i, collection in enumerate(collections):
            print(f"{i+1}. {collection['title']} ({collection['type']}, {collection['count']}个视频)")
            
        choice = int(input("请输入要获取的合集序号: ")) - 1
        if choice < 0 or choice >= len(collections):
            print("无效的选择")
            return
            
        collection_id = collections[choice]['id']
        collection_type = collections[choice]['type']
        collection_title = collections[choice]['title']
        print(f"已选择合集: {collection_title}")
    
    # 获取合集下的所有视频
    videos = get_collection_videos(mid, collection_id, collection_type, cookie_dict=cookie_dict)
    
    # 打印视频数量
    print(f"合集中共有 {len(videos)} 个视频")
    
    # 格式化视频数据，提取模板中需要的字段
    formatted_videos = []
    for video in videos:
        # 先添加基本信息中的字段
        video_data = {
            'aid': video.get('aid'),
            'bvid': video.get('bvid'),
            'title': video.get('title'),
            'desc': video.get('desc'),
            'dynamic': video.get('dynamic'),
            'pic': video.get('pic'),
            'created': video.get('pubdate'),
            'length': video.get('duration'),
            'play': video.get('stat', {}).get('view'),
            'comment': video.get('stat', {}).get('reply'),
        }
        
        # 获取详细信息
        print(f"正在获取视频 {video['bvid']} 的详细信息...")
        detail = get_video_detail(bvid=video['bvid'], cookie_dict=cookie_dict)
        
        # 如果成功获取详细信息，添加额外字段
        if detail and detail.get('code') == 0:
            detail_data = detail.get('data', {})
            
            # 添加UP主信息
            owner = detail_data.get('owner', {})
            video_data.update({
                'author': owner.get('name'),
                'mid': owner.get('mid'),
                'owner_face': owner.get('face')
            })
            
            # 添加统计数据
            stat = detail_data.get('stat', {})
            video_data.update({
                'danmaku': stat.get('danmaku'),
                'favorite': stat.get('favorite'),
                'coin': stat.get('coin'),
                'share': stat.get('share'),
                'like': stat.get('like'),
                'dislike': stat.get('dislike')
            })
        
        formatted_videos.append(video_data)
        time.sleep(1)  # 避免请求过于频繁
    
    # 保存为JSON文件
    collection_type_str = "season" if collection_type == "season" else "series"
    output_file = os.path.join(data_dir, f"up_{mid}_{collection_type_str}_{collection_id}_videos.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_videos, f, ensure_ascii=False, indent=4)
    print(f"视频信息已保存至: {output_file}")

# 以下是从原始代码中保留的辅助函数
def get_wbi_keys():
    """获取WBI密钥，尝试多种方法"""
    # 优先从缓存读取
    img_key, sub_key = load_wbi_keys_from_cache()
    if img_key and sub_key:
        print(f"从缓存加载WBI密钥: img_key={img_key}, sub_key={sub_key}")
        return img_key, sub_key
    
    # 方法1: 从bili_ticket获取
    _, img_key, sub_key = get_bili_ticket()
    if img_key and sub_key:
        save_wbi_keys_to_cache(img_key, sub_key)
        return img_key, sub_key
    
    # 使用默认值
    print("获取WBI密钥失败，使用默认值")
    img_key = "7cd084941338484aae1ad9425b84077c"
    sub_key = "4932caff0ff746eab6f01bf08b70ac45"
    return img_key, sub_key

def get_mixin_key(orig_key):
    # B站混合盐值算法
    salt_chars = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz0123456789"
    # 正确的索引值
    salt_indexes = [46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13]
    
    mixed_key = ""
    for i in salt_indexes:
        if i < len(orig_key):
            mixed_key += orig_key[i]
    return mixed_key

def get_wbi_signature(params, img_key, sub_key):
    # 合并key并计算混合密钥
    mixin_key = get_mixin_key(img_key + sub_key)
    
    # 添加时间戳
    params['wts'] = str(int(time.time()))
    
    # 按照key排序
    sorted_params = dict(sorted(params.items()))
    
    # 过滤特殊字符
    query_items = []
    for k, v in sorted_params.items():
        # 修正：WBI签名需要过滤掉一些特殊字符
        v_str = str(v)
        v_str = ''.join(ch for ch in v_str if ch not in "!'()*")
        query_items.append(f"{k}={v_str}")
    
    query = "&".join(query_items)
    
    # 计算w_rid
    md5 = hashlib.md5()
    md5.update((query + mixin_key).encode())
    params['w_rid'] = md5.hexdigest()
    
    return params

def controlled_request(url, params, cookie_dict=None, delay_range=(2, 5), max_retries=3):
    """发送请求并控制频率"""
    # 获取bili_ticket（如果未提供自定义Cookie）
    bili_ticket = None
    if not cookie_dict:
        bili_ticket, _, _ = get_bili_ticket()
    
    retries = 0
    while retries < max_retries:
        # 随机延时
        sleep_time = random.uniform(*delay_range)
        time.sleep(sleep_time)
        
        # 发送请求
        headers = get_headers(cookie_dict)
        
        # 如果没有提供自定义Cookie，但获取了bili_ticket，则使用它
        if not cookie_dict and bili_ticket:
            if "Cookie" in headers:
                headers["Cookie"] += f"; bili_ticket={bili_ticket}"
            else:
                headers["Cookie"] = f"bili_ticket={bili_ticket}"
        
        response = requests.get(url, params=params, headers=headers)
        
        # 检查是否被拦截
        if response.status_code == 412:
            print("请求被拦截，等待更长时间后重试...")
            time.sleep(random.uniform(30, 60))
            retries += 1
            continue
        
        return response
    
    return None

def get_bili_ticket():
    """获取bili_ticket，同时获取最新的wbi密钥"""
    try:
        ts = int(time.time())
        key = "XgwSnGZ1p"
        message = f"ts{ts}"
        hexsign = hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()
        
        url = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"
        params = {
            "key_id": "ec02",
            "hexsign": hexsign,
            "context[ts]": str(ts),
            "csrf": ""
        }
        
        headers = get_headers()
        headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive"
        })
        
        print(f"正在请求bili_ticket，参数: {params}")
        
        response = requests.post(url, params=params, headers=headers)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if not response.text:
            return None, None, None
            
        data = response.json()
        
        if data.get("code") == 0:
            ticket = data["data"]["ticket"]
            if "nav" in data["data"]:
                img_url = data["data"]["nav"]["img"]
                sub_url = data["data"]["nav"]["sub"]
                img_key = img_url.split("/")[-1].split(".")[0]
                sub_key = sub_url.split("/")[-1].split(".")[0]
                
                if is_valid_wbi_key(img_key) and is_valid_wbi_key(sub_key):
                    print(f"成功获取最新WBI密钥: img_key={img_key}, sub_key={sub_key}")
                    return ticket, img_key, sub_key
            
        return None, None, None
    except Exception as e:
        print(f"获取bili_ticket失败: {e}")
        return None, None, None

def is_valid_wbi_key(key):
    """检查WBI密钥的格式是否正确"""
    # 通常WBI密钥是32位16进制字符串
    if not key or not isinstance(key, str):
        return False
    
    # 检查长度
    if len(key) != 32:
        return False
    
    # 检查是否只包含16进制字符
    try:
        int(key, 16)
        return True
    except ValueError:
        return False
    
    return True

def save_wbi_keys_to_cache(img_key, sub_key):
    """将WBI密钥保存到缓存文件"""
    try:
        # 创建data目录
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        cache_file = os.path.join(data_dir, "wbi_keys_cache.json")
        cache_data = {
            "img_key": img_key,
            "sub_key": sub_key,
            "timestamp": int(time.time())
        }
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(cache_data, f)
        print("WBI密钥已保存到缓存")
    except Exception as e:
        print(f"保存WBI密钥到缓存失败: {e}")

def load_wbi_keys_from_cache():
    """从缓存文件加载WBI密钥"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        cache_file = os.path.join(data_dir, "wbi_keys_cache.json")
        
        if not os.path.exists(cache_file):
            return None, None
            
        with open(cache_file, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
            
            # 检查缓存是否过期（默认24小时）
            if int(time.time()) - cache_data["timestamp"] < 86400:
                return cache_data["img_key"], cache_data["sub_key"]
            else:
                print("缓存的WBI密钥已过期")
    except FileNotFoundError:
        print("WBI密钥缓存文件不存在")
    except Exception as e:
        print(f"从缓存加载WBI密钥失败: {e}")
    
    return None, None

if __name__ == "__main__":
    # 使用 bilibili_cookie_manager 获取 cookie
    cookie_dict = get_cookie()
    
    if not cookie_dict:
        print("没有有效的Cookie，将使用无登录模式请求（可能会受到更多限制）")
        cookie_dict = {}
    
    up_mid = 23947287
    
    # 询问用户是否直接输入合集ID或列出合集让用户选择
    choice = input("是否直接输入合集ID? (y/n): ")
    if choice.lower() == 'y':
        # collection_type = input("输入合集类型 (season/series): ")
        collection_type = 'season'
        collection_id = input("输入合集ID: ")
        main(int(up_mid), collection_id=int(collection_id), collection_type=collection_type, cookie_dict=cookie_dict)
    else:
        main(int(up_mid), cookie_dict=cookie_dict)