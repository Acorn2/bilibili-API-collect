#!/usr/bin/env python3
"""
B站视频信息补充工具
==================

本工具用于补充已有JSON文件中视频的desc和dynamic字段信息。

功能：
1. 读取已有的JSON视频文件
2. 遍历每个视频记录，补充desc和dynamic字段
3. 更新JSON文件，保留原有数据的同时添加新信息
4. 支持断点续传，避免重复请求

使用方法：
1. 运行脚本
2. 指定JSON文件路径
3. 程序自动补充信息并更新文件

技术特性：
- 使用B站API获取视频详细信息
- 请求频率控制，避免触发风控
- 支持Cookie登录，获取更完整数据
- 进度显示和错误处理
"""

import json
import os
import sys
import time
import random
import argparse
from tqdm import tqdm

# 导入单视频爬虫的相关功能
from bilibili_cookie_manager import get_cookie, get_headers
from single_video_spider import get_video_detail, controlled_request

def update_video_info(json_file_path, delay_range=(2, 5), max_retries=3):
    """
    更新JSON文件中视频的详细信息，补充desc和dynamic字段
    
    参数:
    - json_file_path: JSON文件路径
    - delay_range: 请求间隔时间范围(秒)
    - max_retries: 最大重试次数
    """
    # 检查文件是否存在
    if not os.path.exists(json_file_path):
        print(f"错误: 文件 '{json_file_path}' 不存在")
        return False
    
    # 获取cookie
    cookie_dict = get_cookie()
    if not cookie_dict:
        print("警告: 没有有效的Cookie，将使用无登录模式请求（可能会受到更多限制）")
        cookie_dict = {}
    
    # 读取JSON文件
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            videos = json.load(f)
    except json.JSONDecodeError:
        print(f"错误: 文件 '{json_file_path}' 不是有效的JSON格式")
        return False
    except Exception as e:
        print(f"读取文件时出错: {str(e)}")
        return False
    
    if not isinstance(videos, list):
        print(f"错误: 文件内容不是视频列表格式")
        return False
    
    print(f"找到 {len(videos)} 个视频记录")
    updated_count = 0
    already_complete = 0
    failed_count = 0
    
    # 遍历视频列表并更新信息
    for i, video in enumerate(tqdm(videos, desc="更新视频信息")):
        # 跳过已有desc和dynamic的视频
        if video.get('desc') is not None and video.get('dynamic') is not None:
            already_complete += 1
            continue
        
        bvid = video.get('bvid')
        aid = video.get('aid')
        
        if not bvid and not aid:
            print(f"警告: 第{i+1}个视频记录缺少bvid和aid")
            failed_count += 1
            continue
        
        # 随机延时，避免请求过于频繁
        sleep_time = random.uniform(*delay_range)
        time.sleep(sleep_time)
        
        # 获取视频详情
        detail = get_video_detail(bvid=bvid, aid=aid, cookie_dict=cookie_dict)
        
        if not detail or detail.get('code') != 0:
            error_msg = detail.get('message') if detail else '请求失败'
            print(f"获取视频 {bvid or aid} 信息失败: {error_msg}")
            failed_count += 1
            continue
        
        # 提取视频数据
        video_data = detail.get('data', {})
        
        # 更新字段
        video['desc'] = video_data.get('desc')
        video['dynamic'] = video_data.get('dynamic')
        updated_count += 1
    
    # 将更新后的数据写回文件
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=4)
        print(f"\n成功更新 {updated_count} 个视频信息")
        if already_complete > 0:
            print(f"{already_complete} 个视频已有信息，无需更新")
        if failed_count > 0:
            print(f"{failed_count} 个视频更新失败")
        return True
    except Exception as e:
        print(f"写入文件时出错: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='补充B站视频JSON文件中的desc和dynamic字段')
    parser.add_argument('json_file', nargs='?', help='要处理的JSON文件路径')
    parser.add_argument('--delay', type=str, default='2-5', help='请求延迟范围，格式为"最小值-最大值"，默认为"2-5"')
    parser.add_argument('--retries', type=int, default=3, help='失败重试次数，默认为3')
    
    args = parser.parse_args()
    
    # 处理延迟参数
    try:
        min_delay, max_delay = map(float, args.delay.split('-'))
        delay_range = (min_delay, max_delay)
    except:
        print("延迟参数格式错误，使用默认值2-5秒")
        delay_range = (2, 5)
    
    # 如果未提供文件路径，使用交互式输入
    if not args.json_file:
        args.json_file = input("请输入要处理的JSON文件路径: ").strip()
    
    # 处理文件路径
    json_file_path = os.path.abspath(args.json_file)
    
    # 更新视频信息
    update_video_info(json_file_path, delay_range=delay_range, max_retries=args.retries)

if __name__ == "__main__":
    main()