
## 1. UP主视频基本信息 (`up_[mid]_videos.json`)

| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `aid` | 视频的AV号（唯一标识符） | 805521873 |
| `bvid` | 视频的BV号（新版唯一标识符） | "BV1o34y1Q7LM" |
| `title` | 视频标题 | "【士兵突击】不是一个兵王的故事" |
| `description` | 视频简介 | "它由所有触动过你的人，触动过你的事构成的..." |
| `pic` | 视频封面图片URL | "http://i1.hdslb.com/bfs/archive/ea4c224b..." |
| `created` | 视频发布时间（Unix时间戳） | 1631966677 |
| `length` | 视频时长（格式：分:秒） | "66:18" |
| `play` | 播放量 | 2136734 |
| `comment` | 评论数 | 5842 |
| `video_review` | 弹幕数 | 14966 |
| `author` | UP主名称 | "宇文数学-" |
| `mid` | UP主ID | 13265324 |



## 2. 视频详细信息 (`up_[mid]_videos_detail.json`)
| 字段名 | 含义 | 示例值 |
|-------|------|--------|
| `owner.face` | UP主头像URL | "http://i2.hdslb.com/bfs/face/d19fbd75b..." |
| `stat.danmaku` | 弹幕数 | 14966 |
| `stat.favorite` | 收藏数 | 86107 |
| `stat.coin` | 投币数 | 161715 |
| `stat.share` | 分享数 | 19728 |
| `stat.like` | 点赞数 | 129780 |
| `stat.dislike` | 不喜欢数 | 0 |