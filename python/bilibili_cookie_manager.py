#!/usr/bin/env python3
"""
B站Cookie管理模块
功能:
- 加载和保存Cookie
- 检查Cookie有效性
- 自动刷新Cookie
- 提供Cookie字典供其他模块使用
使用:
- 作为独立模块引入到其他Python文件中
- 提供简单API以获取和管理Cookie
"""

import os
import time
import json
import random
import re
import requests
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import binascii

# 默认Cookie - 可以为空字符串
DEFAULT_COOKIE = """buvid3=0F89B1FF-5C5E-5905-3B51-262D96B1B89D85075infoc; b_nut=1715760685; _uuid=35C110C710-9A59-C34D-E4D3-3514B9BAD7B889948infoc; buvid4=FBDE087C-A4D0-2337-BC9B-FA33E631970191450-024051508-3R7ADUTckXdPRXhZSe5vHA%3D%3D; rpdid=|(ull)uJYY|)0J'u~ul~Y|Ym~; buvid_fp_plain=undefined; share_source_origin=copy_web; bmg_af_switch=1; bmg_src_def_domain=i0.hdslb.com; bsource=search_google; header_theme_version=CLOSE; enable_web_push=DISABLE; enable_feed_channel=ENABLE; home_feed_column=5; browser_resolution=1854-934; SESSDATA=a1d089a0%2C1759831774%2Cdd933%2A42CjBzkBVofPpUgRh7dLy0S2eF999YbtfUwnI-YxK2WgXoaBpY7LGNlP7RDUcfUUOPw4MSVkdNMUtnMmFkbnlwb1VfV2ZOdEVyMEdyMkRFUy01TFIxTjBfQmVJemUzU3VhYjJmaXQ0RDhkZWdBWkRla2hIR1dMdmh4OW50VXNGZVA0YXUwdVI2SjF3IIEC; bili_jct=fbd7a3c3fc6a63b39a4d118ce7721c7e; DedeUserID=58333954; DedeUserID__ckMd5=d3ca2c7fca433a27; sid=7ug0li69; b_lsid=D5935655_196220EF641; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDQ1OTExMTcsImlhdCI6MTc0NDMzMTg1NywicGx0IjotMX0.SGxs5hYPJaB4Mon3ABEkFX0R4MZxArdfbGceqUA9IJU; bili_ticket_expires=1744591057; fingerprint=8b07f8647f05a14fc9d44b550d0cb2cb; buvid_fp=0F89B1FF-5C5E-5905-3B51-262D96B1B89D85075infoc; CURRENT_FNVAL=2000; bp_t_offset_58333954=1054398227601686528"""

# 数据存储目录
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# 自定义异常
class CookieError(Exception):
    """Cookie相关错误的基类"""
    pass

class CookieExpiredError(CookieError):
    """Cookie已过期的错误"""
    pass

class CookieRefreshError(CookieError):
    """Cookie刷新失败的错误"""
    pass

def get_headers(cookie_dict=None):
    """生成HTTP请求头"""
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
        "Accept-Encoding": "identity",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    
    # 如果提供了Cookie字典，转换为Cookie字符串
    if cookie_dict and isinstance(cookie_dict, dict) and len(cookie_dict) > 0:
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookie_dict.items()])
        headers["Cookie"] = cookie_str
    
    return headers

def parse_cookie_string(cookie_string):
    """将Cookie字符串解析为字典"""
    cookie_dict = {}
    try:
        for item in cookie_string.split(';'):
            if not item.strip():
                continue
            try:
                key, value = item.strip().split('=', 1)
                cookie_dict[key.strip()] = value.strip()
            except ValueError:
                # 处理没有值的Cookie项
                continue
        
        return cookie_dict
    except Exception as e:
        print(f"解析Cookie出错: {e}")
        return {}

def load_saved_cookies():
    """从文件加载保存的Cookie和refresh_token"""
    try:
        cookie_file = os.path.join(DATA_DIR, "bilibili_cookies.json")
        
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
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        cookie_file = os.path.join(DATA_DIR, "bilibili_cookies.json")
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
            raise CookieExpiredError("Cookie已过期，需要重新登录")
        else:
            print(f"检查Cookie刷新状态失败: {data['message']}")
            return False
    except CookieExpiredError:
        raise
    except Exception as e:
        print(f"检查Cookie刷新状态时出错: {e}")
        return False

def generate_correspond_path(timestamp):
    """生成CorrespondPath"""
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
            # 使用正则表达式获取refresh_csrf
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
            raise CookieRefreshError(f"刷新Cookie失败: {data['message']}")
    except CookieRefreshError:
        raise
    except Exception as e:
        print(f"刷新Cookie时出错: {e}")
        raise CookieRefreshError(f"刷新Cookie时出错: {e}")

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

def get_cookie(input_cookie_string=None, force_refresh=False):
    """
    获取有效的Cookie
    
    参数:
        input_cookie_string: 可选，输入的Cookie字符串
        force_refresh: 是否强制刷新Cookie
        
    返回:
        cookie_dict: 有效的Cookie字典
    """
    # 如果有输入Cookie，解析它
    input_cookie_dict = None
    if input_cookie_string:
        input_cookie_dict = parse_cookie_string(input_cookie_string)
    
    # 加载已保存的Cookie
    saved_cookie_dict, saved_refresh_token = load_saved_cookies()
    
    # 确定使用哪个Cookie
    cookie_dict = input_cookie_dict or saved_cookie_dict
    refresh_token = saved_refresh_token
    
    # 如果没有可用的Cookie，尝试使用默认Cookie
    if not cookie_dict and DEFAULT_COOKIE:
        print("使用默认Cookie")
        cookie_dict = parse_cookie_string(DEFAULT_COOKIE)
    
    # 检查是否有有效的Cookie
    if not cookie_dict or 'SESSDATA' not in cookie_dict or 'bili_jct' not in cookie_dict:
        print("没有有效的Cookie可用")
        return None
    
    try:
        # 检查Cookie是否需要刷新
        refresh_needed = force_refresh or check_cookie_refresh_needed(cookie_dict)
        
        if refresh_needed:
            print("Cookie需要刷新，正在进行刷新...")
            
            if not refresh_token:
                print("缺少refresh_token，无法刷新Cookie")
                return cookie_dict
                
            # 1. 生成CorrespondPath
            timestamp = int(time.time() * 1000)
            correspond_path = generate_correspond_path(timestamp)
            
            # 2. 获取refresh_csrf
            refresh_csrf = get_refresh_csrf(correspond_path, cookie_dict)
            if not refresh_csrf:
                print("获取refresh_csrf失败")
                return cookie_dict
            
            # 3. 刷新Cookie
            new_cookie_dict, new_refresh_token = refresh_cookie(refresh_token, refresh_csrf, cookie_dict)
            
            # 4. 确认更新
            if confirm_refresh(refresh_token, new_cookie_dict):
                print("Cookie刷新成功")
                # 保存新的Cookie和refresh_token
                save_cookies(new_cookie_dict, new_refresh_token)
                return new_cookie_dict
            else:
                print("确认Cookie刷新失败")
                return cookie_dict
        else:
            print("Cookie有效，无需刷新")
            # 如果是新输入的Cookie，保存它
            if input_cookie_dict and input_cookie_dict != saved_cookie_dict:
                save_cookies(input_cookie_dict, refresh_token)
            return cookie_dict
    except CookieExpiredError:
        # Cookie已过期，需要重新登录
        print("Cookie已过期，需要重新登录")
        return None
    except CookieRefreshError as e:
        # 刷新失败，返回原Cookie
        print(f"Cookie刷新失败: {e}")
        return cookie_dict
    except Exception as e:
        # 其他错误，返回原Cookie
        print(f"处理Cookie时出错: {e}")
        return cookie_dict

def verify_cookie(cookie_dict):
    """
    验证Cookie是否有效
    
    参数:
        cookie_dict: Cookie字典
        
    返回:
        bool: Cookie是否有效
    """
    if not cookie_dict or 'SESSDATA' not in cookie_dict or 'bili_jct' not in cookie_dict:
        return False
    
    url = "https://api.bilibili.com/x/web-interface/nav"
    
    try:
        response = requests.get(url, headers=get_headers(cookie_dict))
        data = response.json()
        
        # 检查登录状态
        return data['code'] == 0 and data['data']['isLogin']
    except Exception as e:
        print(f"验证Cookie时出错: {e}")
        return False

def get_user_info(cookie_dict):
    """
    获取用户信息
    
    参数:
        cookie_dict: Cookie字典
        
    返回:
        dict: 用户信息
    """
    if not cookie_dict or 'SESSDATA' not in cookie_dict:
        return None
    
    url = "https://api.bilibili.com/x/web-interface/nav"
    
    try:
        response = requests.get(url, headers=get_headers(cookie_dict))
        data = response.json()
        
        if data['code'] == 0 and data['data']['isLogin']:
            return {
                'uid': data['data']['mid'],
                'uname': data['data']['uname'],
                'face': data['data']['face'],
                'level': data['data']['level_info']['current_level']
            }
        else:
            return None
    except Exception as e:
        print(f"获取用户信息时出错: {e}")
        return None

# 示例代码：如何使用这个模块
if __name__ == "__main__":
    # 获取有效的Cookie
    cookie_dict = get_cookie()
    
    if cookie_dict:
        print("Cookie有效")
        # 获取用户信息
        user_info = get_user_info(cookie_dict)
        if user_info:
            print(f"已登录用户: {user_info['uname']} (UID: {user_info['uid']}) Lv.{user_info['level']}")
        else:
            print("获取用户信息失败")
    else:
        print("无有效Cookie，请重新登录")