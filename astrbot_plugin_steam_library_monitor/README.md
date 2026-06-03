# Steam游戏库监控插件

一个用于监控Steam好友游戏库变动的AstrBot插件，当好友购买新游戏时会自动发送通知，支持图片渲染。

## 功能特性

- 🎮 监控Steam好友游戏库变动
- 🔔 新游戏购买自动通知
- 🖼️ 图片渲染通知（游戏封面+文字）
- ⏰ 定时轮询检查
- 🎯 支持多个好友同时监控
- 📱 支持多群推送

## 安装

1. 将插件文件夹放入AstrBot的 `data/plugins/` 目录
2. 安装依赖：`pip install httpx Pillow`
3. 重启AstrBot或在WebUI中加载插件

## 配置

在AstrBot WebUI的插件配置中设置：

### 必填配置

| 配置项 | 说明 |
|--------|------|
| `steam_api_key` | Steam Web API Key |
| `steam_ids` | 要监控的Steam ID列表 |

### 可选配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `sgdb_api_key` | SteamGridDB API Key（用于获取游戏封面） | 空 |
| `notify_groups` | 推送通知的群号列表 | 空 |
| `poll_interval` | 轮询间隔（分钟） | 30 |
| `enable_notification` | 启用新游戏通知 | true |
| `render_image` | 启用图片渲染通知 | true |

### 配置示例

```json
{
  "steam_api_key": "你的Steam API Key",
  "sgdb_api_key": "你的SGDB API Key",
  "steam_ids": [
    {"steam_id": "76561198203485468", "nickname": "小明"},
    {"steam_id": "76561198012345678", "nickname": ""}
  ],
  "notify_groups": [
    {"group_id": "123456789"},
    {"group_id": "987654321"}
  ],
  "poll_interval": 30,
  "enable_notification": true,
  "render_image": true
}
```

### 获取API Key

1. **Steam Web API Key**（必填）：
   - 访问 https://steamcommunity.com/dev/apikey
   - 使用Steam账号登录
   - 域名填 `localhost`
   - 同意使用条款
   - 复制生成的API Key

2. **SteamGridDB API Key**（可选）：
   - 访问 https://www.steamgriddb.com/profile/preferences/api
   - 注册账号并登录
   - 复制API Key

## 命令

### 查看监控列表
```
/steamlib list
```

### 立即检查游戏库变动
```
/steamlib check
```

### 查看好友详细信息
```
/steamlib info <steam_id>
```

### 显示帮助
```
/steamlib help
```

## 如何获取Steam ID

1. 打开Steam客户端
2. 点击右上角用户名 -> 查看个人资料
3. 点击"编辑个人资料"
4. 个人资料URL中的数字就是Steam ID

或者访问 https://steamid.io/ 进行查询

## 工作原理

1. 插件启动后会定期调用Steam API获取好友的游戏列表
2. 将获取的游戏列表与本地缓存进行比对
3. 发现新增游戏时发送通知
4. 首次添加好友时只记录游戏库，不触发通知

## 图片渲染

当启用图片渲染时，通知会以精美图片的形式发送：
- 左侧显示游戏封面图（从SteamGridDB获取）
- 右侧显示玩家头像和购买信息
- 渐变背景，视觉效果更佳

如果未配置SteamGridDB API Key或获取封面失败，将降级为文本通知。

## 注意事项

- 需要好友的游戏详情设置为"公开"才能获取游戏列表
- Steam API有调用频率限制，建议轮询间隔不低于15分钟
- 插件数据存储在 `data/plugin_data/astrbot_plugin_steam_library_monitor/` 目录

## 依赖

- httpx >= 0.27.0
- Pillow >= 10.0.0

## 许可证

MIT License
