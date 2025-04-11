# B站UP主视频数据字段含义分析

本文档对B站API返回的视频数据字段进行详细解析，方便理解数据结构和含义，以便后续按需获取信息。

## 1. UP主视频基本信息 (`up_[mid]_videos.json`)

这个文件包含UP主视频的基本信息列表，每个视频条目包含以下主要字段：

### 核心视频信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `aid` | 视频的AV号（唯一标识符） | 805521873 |
| `bvid` | 视频的BV号（新版唯一标识符） | "BV1o34y1Q7LM" |
| `title` | 视频标题 | "【士兵突击】不是一个兵王的故事" |
| `description` | 视频简介 | "它由所有触动过你的人，触动过你的事构成的..." |
| `pic` | 视频封面图片URL | "http://i1.hdslb.com/bfs/archive/ea4c224b..." |
| `created` | 视频发布时间（Unix时间戳） | 1631966677 |
| `length` | 视频时长（格式：分:秒） | "66:18" |

### 视频分类信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `typeid` | 视频分区ID | 182 |
| `copyright` | 版权标识（1表示原创，2表示转载） | "1" |

### 视频统计数据
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `play` | 播放量 | 2136734 |
| `comment` | 评论数 | 5842 |
| `video_review` | 弹幕数 | 14966 |

### UP主信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `author` | UP主名称 | "宇文数学-" |
| `mid` | UP主ID | 13265324 |

### 其他属性
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `attribute` | 属性标识（包含多个特性位） | 16512 |
| `is_pay` | 是否付费内容 | 0 |
| `is_union_video` | 是否联合投稿 | 0 |
| `is_avoided` | 是否被屏蔽 | 0 |
| `playback_position` | 上次播放位置（秒） | 79 |
| `is_self_view` | 是否是自己的视频 | false |

## 2. 视频详细信息 (`up_[mid]_videos_detail.json`)

这个文件包含更详细的视频信息，对应于基本信息中的每个视频：

### 基本信息（与基础版相同但更完整）
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `bvid`, `aid`, `title`, `pic` | 与基础信息相同 | - |
| `pubdate` | 发布时间戳 | 1631966677 |
| `ctime` | 创建时间戳 | 1631966677 |
| `duration` | 视频时长（秒） | 3978 |

### 分区与版权信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `tid` | 分区ID | 182 |
| `tid_v2` | 新版分区ID | 2001 |
| `tname` | 分区名称 | "影视杂谈" |
| `tname_v2` | 新版分区名称 | "影视解读" |
| `copyright` | 版权类型 | 1 |

### 作者信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `owner.mid` | UP主ID | 13265324 |
| `owner.name` | UP主名称 | "宇文数学-" |
| `owner.face` | UP主头像URL | "http://i2.hdslb.com/bfs/face/d19fbd75b..." |

### 统计数据（比基础信息更丰富）
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `stat.view` | 播放量 | 2136734 |
| `stat.danmaku` | 弹幕数 | 14966 |
| `stat.reply` | 评论数 | 5842 |
| `stat.favorite` | 收藏数 | 86107 |
| `stat.coin` | 投币数 | 161715 |
| `stat.share` | 分享数 | 19728 |
| `stat.like` | 点赞数 | 129780 |
| `stat.dislike` | 不喜欢数 | 0 |

### 视频分P信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `videos` | 视频分P数量 | 1 |
| `pages` | 视频分P详细信息 | 数组 |
| `pages[].cid` | 分P的ID | 410374580 |
| `pages[].part` | 分P标题 | "士兵突击 定稿8（3）" |
| `pages[].duration` | 分P时长（秒） | 3978 |
| `pages[].dimension` | 分P分辨率信息 | 对象 |

### 荣誉信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `honor_reply.honor` | 获得的荣誉列表 | 数组 |
| `honor_reply.honor[].type` | 荣誉类型 | 4, 7 |
| `honor_reply.honor[].desc` | 荣誉描述 | "热门", "热门收录" |

### 字幕信息
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `subtitle.allow_submit` | 是否允许提交字幕 | false |
| `subtitle.list` | 字幕列表 | 数组 |
| `subtitle.list[].lan` | 字幕语言代码 | "ai-zh" |
| `subtitle.list[].lan_doc` | 字幕语言描述 | "中文（自动生成）" |

### 权限相关
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `rights.download` | 是否可下载 | 1 |
| `rights.no_reprint` | 是否禁止转载 | 1 |
| `rights.autoplay` | 是否自动播放 | 1 |
| `rights.hd5` | 是否有4K或以上清晰度 | 0/1 |

## 数据获取建议

基于这些字段含义，如果你想按需获取信息，可以考虑以下几个常用场景：

### 1. 获取视频基本信息
```python
# 视频标题、BV号、发布时间、时长
video_info = {
    'title': video['title'],
    'bvid': video['bvid'],
    'pubdate': time.strftime('%Y-%m-%d', time.localtime(video['pubdate'])),
    'duration': f"{video['duration']//60}分{video['duration']%60}秒"
}
```

### 2. 获取视频统计数据
```python
# 视频播放量、点赞、投币、收藏、分享数据
stats = {
    'play': video['stat']['view'],
    'like': video['stat']['like'],
    'coin': video['stat']['coin'],
    'favorite': video['stat']['favorite'],
    'share': video['stat']['share']
}
```

### 3. 分析视频表现
```python
# 计算互动率（互动数/播放量）
interaction = video['stat']['like'] + video['stat']['coin'] + video['stat']['favorite']
interaction_rate = interaction / video['stat']['view']
```
```