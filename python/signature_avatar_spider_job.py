#!/usr/bin/env python3
"""
B站UP主签名和头像爬取脚本
=========================

本工具用于定时获取特定B站UP主的个人签名和头像，适合追踪UP主个人资料变化。

功能：
1. 获取指定UP主的个人签名
2. 获取指定UP主的头像链接
3. 记录获取时间，便于追踪变化
4. 自动管理并刷新B站Cookie，提高请求成功率
5. 缓存WBI密钥，优化访问效率

使用场景：
- 定时监控特定UP主资料变化
- 建立UP主资料历史记录
- 可配合crontab或systemd timer实现定时执行

技术特性：
- 支持Cookie自动刷新机制
- 随机延迟请求，模拟真实用户行为
- 错误处理和重试机制，提高稳定性
- 结果以JSON格式保存，便于后续处理

使用方法：
1. 将脚本配置为定时任务
2. 数据将保存在 data/up_{mid}_info.json 文件中
3. 每次运行会更新最新的签名和头像信息

注意事项：
- 请合理设置运行频率，建议每天1-2次
- 抓取数据仅用于个人研究，请尊重UP主隐私
- 需要保持Cookie有效性以获得最佳结果

参考: https://pa.ci/137.html

作者：[您的名字]
日期：[创建日期]
版本：1.0
"""
import requests
import time
import json
import random
import hashlib
import os
# 引入 bilibili_cookie_manager 模块
from bilibili_cookie_manager import get_cookie, get_headers

# 获取WBI密钥
def get_wbi_keys():
    """获取WBI密钥，优先从缓存读取"""
    # 优先从缓存读取
    img_key, sub_key = load_wbi_keys_from_cache()
    if img_key and sub_key:
        print(f"从缓存加载WBI密钥: img_key={img_key}, sub_key={sub_key}")
        return img_key, sub_key
    
    # 使用默认值
    print("使用默认WBI密钥")
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

def get_up_info(mid, cookie_dict=None):
    """获取UP主基本信息"""
    # 基础参数
    params = {
        'mid': mid
    }
    
    # 获取WBI签名
    img_key, sub_key = get_wbi_keys()
    params = get_wbi_signature(params, img_key, sub_key)
    
    # 发送请求
    url = "https://api.bilibili.com/x/space/wbi/acc/info"
    response = controlled_request(url, params, cookie_dict=cookie_dict)
    
    if response is None:
        print(f"获取UP主 {mid} 信息失败，请求超时或被拒绝")
        return None
    
    try:
        data = response.json()
        if data['code'] != 0:
            print(f"获取UP主 {mid} 信息失败，状态码：{data['code']}，信息：{data['message']}")
            return None
            
        # 提取所需信息
        user_data = data['data']
        return {
            'face': user_data.get('face'),  # 头像链接
            'face_create_time': int(time.time()),  # 头像获取时间
            'sign': user_data.get('sign', ''),  # 个人签名
            'sign_create_time': int(time.time())  # 签名获取时间
        }
    except Exception as e:
        print(f"处理UP主 {mid} 数据时出错：{str(e)}")
        return None

def get_user_cookie(default_cookie=None):
    """获取用户输入的Cookie"""
    print("请提供登录B站后的Cookie以减少风控概率")
    print("提示: 登录B站后，按F12打开开发者工具，在Network标签下查看任意请求的Cookie")
    print("按Enter键使用默认Cookie")
    
    cookie_input = input("请粘贴完整Cookie字符串（直接回车则使用默认Cookie）: ").strip()
    
    if not cookie_input and default_cookie:
        print("使用默认Cookie")
        cookie_input = default_cookie
    elif not cookie_input:
        print("未提供Cookie，将使用默认方式请求")
        return {}
    
    # 解析Cookie字符串为字典
    cookie_dict = {}
    try:
        for item in cookie_input.split(';'):
            if not item.strip():
                continue
            try:
                key, value = item.strip().split('=', 1)
                cookie_dict[key.strip()] = value.strip()
            except ValueError:
                # 处理没有值的Cookie项
                continue
        
        # 检查是否包含重要Cookie
        important_cookies = ['bili_jct', 'SESSDATA', 'DedeUserID']
        missing = [c for c in important_cookies if c not in cookie_dict]
        
        if missing:
            print(f"警告: 缺少重要的Cookie: {', '.join(missing)}")
        else:
            print("Cookie格式有效，包含所有重要字段")
        
        return cookie_dict
    except Exception as e:
        print(f"解析Cookie出错: {e}")
        return {}

def check_cookie_refresh_needed(cookie_dict):
    """检查Cookie是否需要刷新"""
    if not cookie_dict or 'SESSDATA' not in cookie_dict or 'bili_jct' not in cookie_dict:
        print("Cookie无效或不完整，无法检查刷新状态")
        return False
    
    url = "https://passport.bilibili.com/x/passport-login/web/cookie/info"
    params = {'csrf': cookie_dict.get('bili_jct', '')}
    
    try:
        response = requests.get(url, params=params, headers=get_headers(cookie_dict))
        data = response.json()
        
        if data['code'] == 0:
            # 检查是否需要刷新
            return data['data']['refresh']
        elif data['code'] == -101:
            print("Cookie已过期，需要重新登录")
            return None  # 表示需要重新登录
        else:
            print(f"检查Cookie刷新状态失败: {data['message']}")
            return False
    except Exception as e:
        print(f"检查Cookie刷新状态时出错: {e}")
        return False

def generate_correspond_path(timestamp):
    """生成CorrespondPath"""
    # 这里需要实现RSA-OAEP加密算法
    # 可以使用第三方库如cryptography或pycryptodome
    # 示例代码(需要安装pycryptodome):
    from Cryptodome.Cipher import PKCS1_OAEP
    from Cryptodome.PublicKey import RSA
    from Cryptodome.Hash import SHA256
    import binascii
    
    # B站公钥
    key = RSA.importKey('''\
    -----BEGIN PUBLIC KEY-----
    MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDLgd2OAkcGVtoE3ThUREbio0Eg
    Uc/prcajMKXvkCKFCWhJYJcLkcM2DKKcSeFpD/j6Boy538YXnR6VhcuUJOhH2x71
    nzPjfdTcqMz7djHum0qSZA0AyCBDABUqCrfNgCiJ00Ra7GmRj+YCK1NJEuewlb40
    JNrRuoEUXpabUzGB8QIDAQAB
    -----END PUBLIC KEY-----''')
    
    cipher = PKCS1_OAEP.new(key, SHA256)
    encrypted = cipher.encrypt(f'refresh_{timestamp}'.encode())
    return binascii.b2a_hex(encrypted).decode()

def get_refresh_csrf(correspond_path, cookie_dict):
    """获取refresh_csrf"""
    url = f"https://www.bilibili.com/correspond/1/{correspond_path}"
    
    try:
        response = requests.get(url, headers=get_headers(cookie_dict))
        
        if response.status_code == 200:
            # 使用简单的HTML解析，也可以使用BeautifulSoup
            import re
            match = re.search(r'<div id="1-name">(.*?)</div>', response.text)
            if match:
                return match.group(1)
        
        print(f"获取refresh_csrf失败，状态码: {response.status_code}")
        return None
    except Exception as e:
        print(f"获取refresh_csrf时出错: {e}")
        return None

def refresh_cookie(refresh_token, refresh_csrf, cookie_dict):
    """刷新Cookie"""
    url = "https://passport.bilibili.com/x/passport-login/web/cookie/refresh"
    
    data = {
        'csrf': cookie_dict.get('bili_jct', ''),
        'refresh_csrf': refresh_csrf,
        'source': 'main_web',
        'refresh_token': refresh_token
    }
    
    try:
        response = requests.post(url, data=data, headers=get_headers(cookie_dict))
        data = response.json()
        
        if data['code'] == 0:
            # 提取响应头中的新Cookie
            new_cookies = {}
            for cookie in response.cookies:
                new_cookies[cookie.name] = cookie.value
            
            # 获取新的refresh_token
            new_refresh_token = data['data']['refresh_token']
            
            return new_cookies, new_refresh_token
        else:
            print(f"刷新Cookie失败: {data['message']}")
            return None, None
    except Exception as e:
        print(f"刷新Cookie时出错: {e}")
        return None, None

def confirm_refresh(old_refresh_token, new_cookie_dict):
    """确认更新Cookie"""
    url = "https://passport.bilibili.com/x/passport-login/web/confirm/refresh"
    
    data = {
        'csrf': new_cookie_dict.get('bili_jct', ''),
        'refresh_token': old_refresh_token
    }
    
    try:
        response = requests.post(url, data=data, headers=get_headers(new_cookie_dict))
        data = response.json()
        
        if data['code'] == 0:
            return True
        else:
            print(f"确认刷新Cookie失败: {data['message']}")
            return False
    except Exception as e:
        print(f"确认刷新Cookie时出错: {e}")
        return False

def load_saved_cookies():
    """从文件加载保存的Cookie和refresh_token"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        cookie_file = os.path.join(data_dir, "bilibili_cookies.json")
        
        if not os.path.exists(cookie_file):
            return None, None
            
        with open(cookie_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("cookies", {}), data.get("refresh_token", "")
    except Exception as e:
        print(f"加载Cookie失败: {e}")
        return None, None

def save_cookies(cookie_dict, refresh_token):
    """保存Cookie和refresh_token到文件"""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        cookie_file = os.path.join(data_dir, "bilibili_cookies.json")
        data = {
            "cookies": cookie_dict,
            "refresh_token": refresh_token,
            "timestamp": int(time.time())
        }
        
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print("Cookie已保存到文件")
        return True
    except Exception as e:
        print(f"保存Cookie失败: {e}")
        return False

def manage_cookies(input_cookie_dict=None):
    """管理Cookie，检查是否需要刷新并进行刷新"""
    # 优先尝试加载已保存的Cookie
    saved_cookie_dict, saved_refresh_token = load_saved_cookies()
    
    # 确定使用哪个Cookie
    cookie_dict = input_cookie_dict or saved_cookie_dict
    refresh_token = None
    
    if saved_refresh_token and saved_cookie_dict and 'SESSDATA' in saved_cookie_dict:
        print("使用已保存的Cookie进行验证")
        refresh_token = saved_refresh_token
    elif input_cookie_dict and 'SESSDATA' in input_cookie_dict:
        print("使用新输入的Cookie")
        # 新输入的Cookie没有refresh_token，后续需从登录接口获取
    else:
        print("没有有效的Cookie可用")
        return None
    
    # 检查Cookie是否需要刷新
    refresh_needed = check_cookie_refresh_needed(cookie_dict)
    
    if refresh_needed is None:  # Cookie已过期
        print("Cookie已过期，需要重新登录")
        return None
    elif refresh_needed:  # 需要刷新
        print("Cookie需要刷新，正在进行刷新...")
        
        # 1. 生成CorrespondPath
        timestamp = int(time.time() * 1000)
        correspond_path = generate_correspond_path(timestamp)
        
        # 2. 获取refresh_csrf
        refresh_csrf = get_refresh_csrf(correspond_path, cookie_dict)
        if not refresh_csrf:
            print("获取refresh_csrf失败")
            return cookie_dict  # 返回原Cookie
        
        # 3. 刷新Cookie
        new_cookie_dict, new_refresh_token = refresh_cookie(refresh_token, refresh_csrf, cookie_dict)
        if not new_cookie_dict:
            print("刷新Cookie失败")
            return cookie_dict  # 返回原Cookie
        
        # 4. 确认更新
        if confirm_refresh(refresh_token, new_cookie_dict):
            print("Cookie刷新成功")
            # 保存新的Cookie和refresh_token
            save_cookies(new_cookie_dict, new_refresh_token)
            return new_cookie_dict
        else:
            print("确认Cookie刷新失败")
            return cookie_dict  # 返回原Cookie
    else:
        print("Cookie有效，无需刷新")
        # 如果输入了新Cookie，保存它
        if input_cookie_dict and input_cookie_dict != saved_cookie_dict:
            save_cookies(input_cookie_dict, refresh_token)
        return cookie_dict

def main():
    # 创建data目录
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"创建data目录: {data_dir}")
    
    # 使用 bilibili_cookie_manager 获取 cookie
    active_cookie_dict = get_cookie()
    
    if not active_cookie_dict:
        print("没有有效的Cookie，将使用无登录模式请求（可能会受到更多限制）")
        active_cookie_dict = {}
    
    # 获取UP主mid
    up_mid = 13265324
    
    try:
        # 获取UP主信息
        print(f"正在获取UP主 {up_mid} 的信息...")
        up_info = get_up_info(up_mid, cookie_dict=active_cookie_dict)
        
        if up_info:
            # 保存为JSON文件
            output_file = os.path.join(data_dir, f"up_{up_mid}_info.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(up_info, f, ensure_ascii=False, indent=4)
            print(f"UP主 {up_mid} 的签名和头像信息已保存至: {output_file}")
            
            # 打印获取到的信息
            print("\nUP主信息摘要:")
            print(f"头像链接: {up_info['face']}")
            print(f"个人签名: {up_info['sign']}")
        else:
            print(f"获取UP主 {up_mid} 的信息失败")
    except Exception as e:
        print(f"处理过程中出错: {e}")

if __name__ == "__main__":
    main()