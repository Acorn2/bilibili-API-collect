#!/usr/bin/env python3
"""
B站UP主全部视频数据抓取工具
============================

本工具用于抓取B站特定UP主的所有视频数据信息。

功能：
1. 获取指定UP主的所有视频列表
2. 获取每个视频的详细数据（标题、播放量、点赞、投币等）
3. 支持WBI签名验证，应对B站的API访问限制
4. 处理风控验证，提高数据抓取成功率
5. 结果以JSON格式保存，方便后续分析和处理

使用方法：
1. 运行脚本后输入UP主的mid（用户ID）
2. 程序会自动获取该UP主的所有视频信息
3. 数据将保存在 data 目录下的 up_{mid}_videos_combined.json 文件中

技术特性：
- 自动控制请求频率，避免触发风控
- 支持Cookie登录，减少限制
- 缓存WBI密钥，提高请求效率
- 自动重试机制，提高抓取成功率

注意事项：
- 请勿频繁使用，以免对B站服务器造成压力
- 抓取的数据仅供个人学习和研究使用
- 大量视频的UP主可能需要较长时间完成抓取

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

# 获取UP主所有视频信息
def get_up_videos(mid, cookie_dict=None, max_pages=100):
    all_videos = []
    page = 1
    
    while True:
        # 基础参数
        params = {
            'mid': mid,
            'pn': page,
            'ps': 30,
            'order': 'pubdate',  # 发布时间排序
            'platform': 'web',
            'web_location': '333.999',
            'tid': 0,
            'keyword': '',
            'unique_k': ''
        }
        
        # 获取WBI签名
        img_key, sub_key = get_wbi_keys()
        params = get_wbi_signature(params, img_key, sub_key)
        
        # 发送请求
        url = "https://api.bilibili.com/x/space/wbi/arc/search"
        response = controlled_request(url, params, cookie_dict=cookie_dict)
        
        if response is None:
            print(f"第{page}页请求失败，尝试继续下一页")
            page += 1
            if page > max_pages:
                break
            continue
            
        try:
            data = response.json()
            if data['code'] != 0 or not data['data'].get('list', {}).get('vlist'):
                print(f"获取第{page}页失败或已无更多视频，状态码：{data['code']}")
                break
                
            # 提取视频信息
            videos = data['data']['list']['vlist']
            all_videos.extend(videos)
            print(f"成功获取第{page}页，共{len(videos)}个视频")
            
            # 检查是否有更多页
            if len(videos) < 30 or page >= max_pages:
                break
                
            page += 1
        except Exception as e:
            print(f"处理第{page}页数据时出错：{str(e)}")
            break
        
    return all_videos

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
def main(mid, cookie_dict=None):
    # 创建data目录
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"创建data目录: {data_dir}")
    
    # 获取UP主所有视频
    videos = get_up_videos(mid, cookie_dict=cookie_dict)
    
    # 打印视频数量
    print(f"UP主 {mid} 共有 {len(videos)} 个视频")
    
    # 格式化视频数据，提取模板中需要的字段
    formatted_videos = []
    for video in videos:
        # 先添加基本信息中的字段
        video_data = {
            'aid': video.get('aid'),
            'bvid': video.get('bvid'),
            'title': video.get('title'),
            'desc': video.get('description'),  # 修改为 desc 以保持一致
            'pic': video.get('pic'),
            'created': video.get('created'),
            'length': video.get('length'),
            'play': video.get('play'),
            'comment': video.get('comment'),
            'video_review': video.get('video_review'),
            'author': video.get('author'),
            'mid': video.get('mid')
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
            
            # 添加动态信息
            video_data['dynamic'] = detail_data.get('dynamic')
            
            # 添加分区信息
            if 'tid' in detail_data:
                video_data['tid'] = detail_data.get('tid')
                video_data['tname'] = detail_data.get('tname')
            
            # 添加CID
            video_data['cid'] = detail_data.get('cid')
            
            # 添加视频标签
            if 'tag' in detail_data:
                video_data['tags'] = detail_data.get('tag').split(',')
        
        formatted_videos.append(video_data)
        time.sleep(1)  # 避免请求过于频繁
    
    # 保存为单个JSON文件
    output_file = os.path.join(data_dir, f"up_{mid}_videos_combined.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_videos, f, ensure_ascii=False, indent=4)
    print(f"视频信息已保存至: {output_file}")

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
    # B站混合盐值算法 - 修正为正确的实现
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

def get_headers(cookie_dict=None):
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    ]
    
    headers = {
        "User-Agent": random.choice(user_agents),
        "Referer": "https://www.bilibili.com/",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.bilibili.com",
        "Accept-Encoding": "identity",  # 只接受未压缩的内容
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    # 如果提供了Cookie字典，转换为Cookie字符串
    if cookie_dict and isinstance(cookie_dict, dict) and len(cookie_dict) > 0:
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
        headers["Cookie"] = cookie_str
    
    return headers

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

def handle_gaia_vtoken(response, cookie_dict=None):
    """处理风控校验失败的情况"""
    if response.status_code == 200:
        try:
            data = response.json()
            if data.get("code") == -352:
                v_voucher = data.get("data", {}).get("v_voucher")
                if not v_voucher:
                    headers = response.headers
                    v_voucher = headers.get("x-bili-gaia-vvoucher")
                
                if v_voucher:
                    print(f"遇到风控校验，v_voucher: {v_voucher}")
                    
                    # 如果有Cookie，尝试自动处理验证码
                    if cookie_dict and len(cookie_dict) > 0:
                        if handle_v_voucher(v_voucher, cookie_dict):
                            print("验证码处理成功")
                            return False  # 不需要重试
                    
                    print("请手动处理风控验证，参考 bili_ticket.md 和 v_voucher.md 文档")
                    return True  # 需要重试
        except Exception as e:
            print(f"处理风控验证出错: {e}")
    return False

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

# 全局变量用于存储WBI密钥
img_key, sub_key = None, None

def verify_wbi_keys(img_key, sub_key):
    """验证WBI密钥是否正确可用"""
    try:
        params = {
            'limit': 10,
            'ps': 10,
            'pn': 1
        }
        
        signed_params = get_wbi_signature(params, img_key, sub_key)
        url = "https://api.bilibili.com/x/web-interface/wbi/search/square"
        headers = get_headers()
        response = requests.get(url, params=signed_params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') == 0:
                print(f"WBI密钥验证成功: img_key={img_key}, sub_key={sub_key}")
                return True
        
        return False
    except Exception as e:
        print(f"WBI密钥验证失败: {e}")
        return False

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

def log_wbi_key_event(event_type, details):
    """记录WBI密钥相关事件"""
    try:
        # 创建data目录
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        log_file = os.path.join(data_dir, "wbi_keys_log.txt")
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            f.write(f"[{timestamp}] {event_type}: {details}\n")
    except Exception as e:
        print(f"记录日志失败: {e}")

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

def handle_v_voucher(v_voucher, cookie_dict=None):
    """尝试自动处理v_voucher验证"""
    try:
        print(f"正在尝试处理风控验证: {v_voucher}")
        
        # 构造请求
        url = "https://api.bilibili.com/x/gaia-vgate/v1/register"
        params = {
            "csrf": cookie_dict.get("bili_jct", ""),
            "v_voucher": v_voucher
        }
        
        headers = get_headers(cookie_dict)
        headers.update({
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://www.bilibili.com",
            "Referer": "https://www.bilibili.com/"
        })
        
        # 发送请求获取验证信息
        response = requests.post(url, data=params, headers=headers)
        data = response.json()
        
        if data["code"] == 0 and data["data"]["type"] == "geetest":
            print("需要人工完成验证码，请在浏览器中登录后重试")
            print(f"验证信息: {data['data']}")
            # 获取验证码信息
            token = data["data"]["token"]
            challenge = data["data"]["geetest"]["challenge"]
            gt = data["data"]["geetest"]["gt"]
            
            # 实际环境中这里可以集成自动验证码识别服务
            print(f"验证码token: {token}")
            print(f"验证码challenge: {challenge}")
            print(f"验证码gt: {gt}")
            print("请手动在浏览器中处理验证码后重试")
            
            # 等待人工介入
            time.sleep(30)
            return False
        else:
            print(f"获取验证码信息失败: {data}")
            return False
    except Exception as e:
        print(f"处理验证码过程出错: {e}")
        return False

if __name__ == "__main__":
    # 使用 bilibili_cookie_manager 获取 cookie
    cookie_dict = get_cookie()
    
    if not cookie_dict:
        print("没有有效的Cookie，将使用无登录模式请求（可能会受到更多限制）")
        cookie_dict = {}
    
    up_mid = input("请输入UP主的mid: ")
    main(int(up_mid), cookie_dict=cookie_dict)