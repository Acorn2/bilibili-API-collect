import re
import requests
from bs4 import BeautifulSoup
from openpyxl import Workbook
import os
import time
import json  # 导入json模块

def write_error_log(message):
    # 确保错误日志也保存到data目录
    error_log_path = os.path.join(data_dir, "video_errorlist.txt")
    with open(error_log_path, "a", encoding="utf-8") as file:
        file.write(message + "\n")

def is_url(video_id_or_url):
    return video_id_or_url.startswith("http") or video_id_or_url.startswith("https")

def get_video_url(video_id_or_url):
    if is_url(video_id_or_url):
        return video_id_or_url
    else:
        return f"https://www.bilibili.com/video/{video_id_or_url}"

# 保存数据为JSON文件
def save_to_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"数据已保存到JSON文件: {filepath}")

# 获取当前脚本的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))
# 构建输入文件的绝对路径
input_file = os.path.join(script_dir, "idlist-sample.txt")

# 创建data目录路径
data_dir = os.path.join(script_dir, "data")
# 确保data目录存在
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

# 将输出文件路径设置到data目录下
output_excel_file = os.path.join(data_dir, "output-sample.xlsx")
output_json_file = os.path.join(data_dir, "output-sample.json")

# 准备Excel文件
new_wb = Workbook()
new_ws = new_wb.active
column_headers = ["标题", "链接", "up主", "up主id", "精确播放数", "历史累计弹幕数", "点赞数", "投硬币枚数", "收藏人数", "转发人数",
                 "发布时间", "视频时长(秒)", "视频简介", "作者简介", "标签", "视频aid"]
new_ws.append(column_headers)

# 准备JSON数据结构
json_data = []

with open(input_file, "r", encoding="utf-8") as file:
    id_list = file.readlines()

i = 0
for video_id_or_url in id_list:
    i += 1
    url = get_video_url(video_id_or_url.strip())
    try:
        # 添加请求头，模拟浏览器访问
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.bilibili.com/"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # 修复废弃警告：将text参数改为string参数
        initial_state_script = soup.find("script", string=re.compile("window.__INITIAL_STATE__"))
        
        # 检查是否找到脚本
        if initial_state_script is None:
            write_error_log(f"第{i}行视频未找到INITIAL_STATE数据：{url}")
            print(f"第{i}行视频未找到INITIAL_STATE数据，可能是页面结构变化：{url}")
            continue  # 跳过当前视频，继续下一个
            
        initial_state_text = initial_state_script.string

        author_id_pattern = re.compile(r'"mid":(\d+)')
        video_aid_pattern = re.compile(r'"aid":(\d+)')
        video_duration_pattern = re.compile(r'"duration":(\d+)')
        
        # 增加异常处理，避免找不到正则匹配时程序崩溃
        author_id_match = author_id_pattern.search(initial_state_text)
        video_aid_match = video_aid_pattern.search(initial_state_text)
        video_duration_match = video_duration_pattern.search(initial_state_text)
        
        if not all([author_id_match, video_aid_match, video_duration_match]):
            write_error_log(f"第{i}行视频缺少必要信息：{url}")
            print(f"第{i}行视频缺少必要信息，跳过处理：{url}")
            continue
            
        author_id = author_id_match.group(1)
        video_aid = video_aid_match.group(1)
        video_duration_raw = int(video_duration_match.group(1))
        video_duration = video_duration_raw - 2

        # 提取标题
        title_element = soup.find("title")
        if title_element:
            title_raw = title_element.text
            title = re.sub(r"_哔哩哔哩_bilibili", "", title_raw).strip()
        else:
            title = "未找到标题"

        # 提取标签
        keywords_element = soup.find("meta", itemprop="keywords")
        if keywords_element and "content" in keywords_element.attrs:
            keywords_content = keywords_element["content"]
            content_without_title = keywords_content.replace(title + ',', '')
            keywords_list = content_without_title.split(',')
            tags = ",".join(keywords_list[:-4])
        else:
            tags = "未找到标签"

        meta_desc_element = soup.find("meta", itemprop="description")
        if meta_desc_element and "content" in meta_desc_element.attrs:
            meta_description = meta_desc_element["content"]
            
            numbers = re.findall(
                r'[\s\S]*?视频播放量 (\d+)、弹幕量 (\d+)、点赞数 (\d+)、投硬币枚数 (\d+)、收藏人数 (\d+)、转发人数 (\d+)',
                meta_description)

            # 提取作者
            author_search = re.search(r"视频作者\s*([^,]+)", meta_description)
            if author_search:
                author = author_search.group(1).strip()
            else:
                author = "未找到作者"

            # 提取作者简介
            author_desc_pattern = re.compile(r'作者简介 (.+?),')
            author_desc_match = author_desc_pattern.search(meta_description)
            if author_desc_match:
                author_desc = author_desc_match.group(1)
            else:
                author_desc = "未找到作者简介"

            # 提取视频简介
            meta_parts = re.split(r',\s*', meta_description)
            if meta_parts:
                video_desc = meta_parts[0].strip()
            else:
                video_desc = "未找到视频简介"
        else:
            numbers = []
            author = "未找到作者"
            author_desc = "未找到作者简介"
            video_desc = "未找到视频简介"

        if numbers:
            views, danmaku, likes, coins, favorites, shares = [int(n) for n in numbers[0]]
            publish_date_element = soup.find("meta", itemprop="uploadDate")
            publish_date = publish_date_element["content"] if publish_date_element else "未找到发布日期"
            
            # 创建视频数据列表（用于Excel）和字典（用于JSON）
            video_data = [title, url, author, author_id, views, danmaku, likes, coins, favorites, shares, publish_date, video_duration, video_desc, author_desc, tags, video_aid]
            
            # 添加到Excel工作表
            new_ws.append(video_data)
            
            # 创建JSON数据对象并添加到列表
            video_json = {
                "title": title,
                "url": url,
                "author": author,
                "author_id": author_id,
                "views": views,
                "danmaku": danmaku,
                "likes": likes,
                "coins": coins,
                "favorites": favorites,
                "shares": shares,
                "publish_date": publish_date,
                "duration": video_duration,
                "description": video_desc,
                "author_description": author_desc,
                "tags": tags,
                "aid": video_aid,
                "bvid": video_id_or_url.strip() if video_id_or_url.strip().startswith("BV") else ""
            }
            json_data.append(video_json)
            
            print(f"第{i}行视频{url}已完成爬取")
        else:
            print(f"第{i}行视频 {url}未找到相关数据，可能为分集视频")
            
        # 每爬取一定数量视频，保存进度
        if i % 5 == 0:  # 每处理5个视频保存一次
            # 保存Excel
            new_wb.save(output_excel_file)
            # 保存JSON
            save_to_json(json_data, output_json_file)
            print(f"已保存当前进度")
            
        # 添加延时，避免请求过于频繁被B站限制
        time.sleep(2)  # 延时2秒

    except Exception as e:
        write_error_log(f"第{i}行视频发生错误：{str(e)}")
        print(f"第{i}行发生错误，已记录到错误日志:出错数据为{video_id_or_url}")
        # 保存当前进度
        new_wb.save(output_excel_file)
        save_to_json(json_data, output_json_file)

# 最终保存
# new_wb.save(output_excel_file)
save_to_json(json_data, output_json_file)
print(f"所有数据已处理完毕，结果已保存为Excel和JSON格式")
print(f"Excel文件: {output_excel_file}")
print(f"JSON文件: {output_json_file}")
