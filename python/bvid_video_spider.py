"""
B站视频信息批量抓取工具
===========================

本工具用于根据BV号列表批量抓取B站视频的详细信息。

功能：
1. 支持从文件或直接输入BV号列表获取视频信息
2. 获取视频的详细数据（标题、播放量、点赞、投币等数据）
3. 将数据保存为JSON格式方便后续分析

使用方法：
1. 直接运行脚本，使用默认BV号列表
2. 或者通过文件导入BV号列表
3. 抓取所有视频数据并保存到json文件

版本：1.0
"""

import requests
import time
import json
import random
import os
import sys
from bilibili_cookie_manager import get_cookie, get_headers

# 默认的BV号列表
DEFAULT_BVIDS = [
    "BV1bR4y1x7RP", "BV1pVrWY2EJK", "BV1h1421t7Fc", "BV1aD421M71A", 
    "BV112421A7pE", "BV14g4y1r71P", "BV1DC4y1q7db", "BV18u411j7EX", 
    "BV1rM4y1e7XK", "BV1Qv4y177CS", "BV1boyzYVEge", "BV1A8411w723", 
    "BV1Z8411A74n", "BV1VV4y1P76f", "BV1kv4y1d7Y8", "BV1Je4y1W7Qn", 
    "BV1Wm4y1w7F3", "BV1aV4y1N71f", "BV11t4y1J7wU", "BV1Rg411Z7LV", 
    "BV16a411S7cy", "BV1Sa411W7fw", "BV1cT411573g", "BV1vY4y147Nk", 
    "BV1dR4y1N7Qx", "BV1x94y1f7x4", "BV13Y411n7Dd", "BV1c34y127nL", 
    "BV1aa411r7aQ", "BV1vQ4y1U79r", "BV1fq4y1z7q1", "BV1oq4y1Z71x", 
    "BV1W64y1U71j", "BV11i4y1L7QQ","BV1NZ421T7Fa","BV1pH4y1k7EJ",
    "BV16a4y1Q7by","BV1cG4y147t7","BV1h94y1X7GT","BV1ia411j7Eq",
    "BV1o54y1f7JM","BV1gb4y1U7vV","BV1qq4y1j7Lt","BV1UV411Y7hA"
]

# 获取单个视频的详细信息
def get_video_detail(bvid, cookie_dict=None):
    """获取单个视频的详细信息"""
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {'bvid': bvid}
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
            time.sleep(random.uniform(15, 30))
            retries += 1
            continue
        
        return response
    
    print(f"请求失败，已尝试{max_retries}次")
    return None

def load_bvids_from_file(file_path):
    """从文件加载BV号列表"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            bvids = [line.strip() for line in f if line.strip().startswith("BV")]
        return bvids
    except Exception as e:
        print(f"从文件加载BV号失败: {e}")
        return []

def save_data_to_json(data, filename="video_data.json"):
    """保存数据到JSON文件"""
    # 创建data目录
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"创建data目录: {data_dir}")
    
    output_file = os.path.join(data_dir, filename)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"数据已保存至: {output_file}")
    return output_file

def fetch_videos_data(bvids, cookie_dict=None):
    """批量获取视频数据"""
    video_data_list = []
    success_count = 0
    failed_count = 0
    
    print(f"开始获取{len(bvids)}个视频的数据...")
    
    for index, bvid in enumerate(bvids):
        print(f"[{index+1}/{len(bvids)}] 正在获取视频 {bvid} 的信息...")
        
        detail = get_video_detail(bvid, cookie_dict)
        
        if detail and detail.get('code') == 0:
            detail_data = detail.get('data', {})
            
            # 提取视频基本信息
            video_data = {
                'aid': detail_data.get('aid'),
                'bvid': detail_data.get('bvid'),
                'title': detail_data.get('title'),
                'desc': detail_data.get('desc'),
                'dynamic': detail_data.get('dynamic'),
                'pic': detail_data.get('pic'),
                'created': detail_data.get('pubdate'),
                'length': detail_data.get('duration'),
                'cid': detail_data.get('cid')
            }
            
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
                'play': stat.get('view'),
                'danmaku': stat.get('danmaku'),
                'favorite': stat.get('favorite'),
                'coin': stat.get('coin'),
                'share': stat.get('share'),
                'like': stat.get('like'),
                'dislike': stat.get('dislike'),
                'comment': stat.get('reply'),
            })
            
            # 添加分区信息
            if 'tid' in detail_data:
                video_data['tid'] = detail_data.get('tid')
                video_data['tname'] = detail_data.get('tname')
            
            # 添加视频标签
            if 'tag' in detail_data:
                video_data['tags'] = detail_data.get('tag').split(',')
            
            video_data_list.append(video_data)
            success_count += 1
            print(f"成功获取视频信息: {video_data['title']}")
        else:
            failed_count += 1
            error_msg = detail.get('message') if detail else "未知错误"
            print(f"获取视频 {bvid} 信息失败: {error_msg}")
        
        # 避免请求过于频繁
        time.sleep(random.uniform(1, 2.5))
    
    print(f"\n数据获取完成！成功: {success_count}, 失败: {failed_count}")
    return video_data_list

def main():
    # 使用 bilibili_cookie_manager 获取 cookie
    cookie_dict = get_cookie()
    
    if not cookie_dict:
        print("没有有效的Cookie，将使用无登录模式请求（可能会受到更多限制）")
        cookie_dict = {}
    
    # 获取BV号列表
    print("请选择BV号来源：")
    print("1. 使用默认BV号列表")
    print("2. 从文件导入BV号列表")
    choice = input("请输入选择 (默认为1): ").strip() or "1"
    
    bvids = []
    if choice == "1":
        bvids = DEFAULT_BVIDS
        print(f"使用默认BV号列表，共{len(bvids)}个视频")
    elif choice == "2":
        file_path = input("请输入BV号文件路径: ").strip()
        if not file_path:
            print("文件路径为空，使用默认BV号列表")
            bvids = DEFAULT_BVIDS
        else:
            bvids = load_bvids_from_file(file_path)
            if not bvids:
                print("从文件加载BV号失败或文件为空，使用默认BV号列表")
                bvids = DEFAULT_BVIDS
            else:
                print(f"从文件加载BV号列表成功，共{len(bvids)}个视频")
    else:
        print("无效的选择，使用默认BV号列表")
        bvids = DEFAULT_BVIDS
    
    # 获取视频数据
    video_data = fetch_videos_data(bvids, cookie_dict)
    
    # 生成当前时间戳作为文件名的一部分
    timestamp = int(time.time())
    filename = f"video_data_{timestamp}.json"
    
    # 保存数据
    if video_data:
        save_data_to_json(video_data, filename)
    else:
        print("没有获取到任何视频数据，不进行保存")

if __name__ == "__main__":
    main()