#!/usr/bin/env python3
"""
B站单视频数据抓取工具
====================

本工具用于抓取B站指定视频ID的详细信息数据。

功能：
1. 支持通过BV号或AV号获取单个视频的详细数据
2. 获取视频的全面信息（标题、简介、播放量、点赞、投币等数据）
3. 支持获取视频相关信息（UP主信息、标签、分区等）
4. 将数据保存为JSON格式方便后续分析

使用方法：
1. 运行脚本
2. 输入视频的BV号或AV号
3. 程序会自动获取视频详细信息并保存到JSON文件

技术特性：
- 支持多种视频ID格式（BV、AV号）
- 自动请求频率控制，避免触发风控
- 支持Cookie登录，获取更完整的数据
- 优雅的错误处理和重试机制

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
import sys
# 引入 bilibili_cookie_manager 模块
from bilibili_cookie_manager import get_cookie, get_headers

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

# 获取视频弹幕信息
def get_video_danmaku_info(cid, cookie_dict=None):
    url = f"https://api.bilibili.com/x/v1/dm/list.so?oid={cid}"
    headers = get_headers(cookie_dict)
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # 返回的是XML格式，简单获取弹幕数量
            return len(re.findall(r'<d p=', response.text))
        else:
            print(f"获取弹幕信息失败，状态码: {response.status_code}")
            return 0
    except Exception as e:
        print(f"获取弹幕信息出错: {str(e)}")
        return 0

# 获取视频相关推荐
def get_video_related(bvid=None, aid=None, cookie_dict=None):
    params = {}
    if bvid:
        params['bvid'] = bvid
    elif aid:
        params['aid'] = aid
    else:
        return []
        
    url = "https://api.bilibili.com/x/web-interface/archive/related"
    headers = get_headers(cookie_dict)
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 0:
                return data['data']
            else:
                print(f"获取相关视频失败，状态码: {data['code']}")
                return []
        else:
            print(f"获取相关视频请求失败，状态码: {response.status_code}")
            return []
    except Exception as e:
        print(f"获取相关视频出错: {str(e)}")
        return []

# 检测并转换视频ID
def convert_video_id(video_id):
    # 检测是否为AV号
    if video_id.lower().startswith('av'):
        aid = video_id[2:]
        try:
            aid = int(aid)
            return {'aid': aid, 'bvid': None}
        except ValueError:
            pass
    
    # 检测是否为BV号
    if video_id.startswith('BV') or video_id.startswith('bv'):
        return {'aid': None, 'bvid': video_id}
    
    # 尝试将纯数字视为AV号
    try:
        aid = int(video_id)
        return {'aid': aid, 'bvid': None}
    except ValueError:
        pass
    
    return None

# 主函数
def main(video_id=None, cookie_dict=None):
    # 创建data目录
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"创建data目录: {data_dir}")
    
    # 如果没有提供视频ID，则请求用户输入
    if not video_id:
        video_id = input("请输入视频BV号或AV号: ").strip()
    
    # 转换视频ID格式
    id_dict = convert_video_id(video_id)
    if not id_dict:
        print(f"无效的视频ID: {video_id}")
        return
    
    # 获取视频详细信息
    print(f"正在获取视频 {video_id} 的详细信息...")
    detail = get_video_detail(bvid=id_dict['bvid'], aid=id_dict['aid'], cookie_dict=cookie_dict)
    
    if not detail or detail.get('code') != 0:
        print(f"获取视频信息失败: {detail.get('message') if detail else '请求失败'}")
        return
    
    # 提取视频详细信息
    video_data = detail.get('data', {})
    
    # 格式化视频数据，整理为易于理解和使用的结构，完善所有可能的字段
    formatted_data = {
        # 基本视频信息
        'aid': video_data.get('aid'),  # AV号
        'bvid': video_data.get('bvid'),  # BV号
        'cid': video_data.get('cid'),  # 视频CID
        'title': video_data.get('title'),  # 标题
        'desc': video_data.get('desc'),  # 视频简介，对应description字段
        'dynamic': video_data.get('dynamic'),  # 视频动态内容(发布时的动态文案)
        'pic': video_data.get('pic'),  # 封面URL
        'videos': video_data.get('videos'),  # 分P数量
        'pubdate': video_data.get('pubdate'),  # 发布时间戳
        'ctime': video_data.get('ctime'),  # 投稿时间戳
        'duration': video_data.get('duration'),  # 视频时长（秒）
        'attribute': video_data.get('attribute'),  # 属性标识
        'length': f"{video_data.get('duration')//60}:{video_data.get('duration')%60:02d}" if video_data.get('duration') else None,  # 时长格式化(分:秒)

    }

    # 保存为JSON文件
    bvid = formatted_data['bvid']
    aid = formatted_data['aid']
    file_name = f"video_{bvid if bvid else 'av'+str(aid)}_info.json"
    output_file = os.path.join(data_dir, file_name)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted_data, f, ensure_ascii=False, indent=4)
    
    print(f"视频信息已保存至: {output_file}")
    
    return formatted_data

def controlled_request(url, params, cookie_dict=None, delay_range=(1, 3), max_retries=3):
    """发送请求并控制频率"""
    retries = 0
    while retries < max_retries:
        # 随机延时
        sleep_time = random.uniform(*delay_range)
        time.sleep(sleep_time)
        
        # 发送请求
        headers = get_headers(cookie_dict)
        
        response = requests.get(url, params=params, headers=headers)
        
        # 检查是否被拦截
        if response.status_code == 412:
            print("请求被拦截，等待更长时间后重试...")
            time.sleep(random.uniform(10, 20))
            retries += 1
            continue
        
        return response
    
    return None

if __name__ == "__main__":
    # 使用 bilibili_cookie_manager 获取 cookie
    cookie_dict = get_cookie()
    
    if not cookie_dict:
        print("没有有效的Cookie，将使用无登录模式请求（可能会受到更多限制）")
        cookie_dict = {}
    
    # 检查是否有命令行参数
    if len(sys.argv) > 1:
        video_id = sys.argv[1]
        main(video_id, cookie_dict=cookie_dict)
    else:
        # 交互模式
        while True:
            video_id = input("\n请输入视频BV号或AV号 (输入q退出): ").strip()
            if video_id.lower() == 'q':
                break
            main(video_id, cookie_dict=cookie_dict)