# Steam游戏库监控插件

一个用于监控Steam好友游戏库变动的AstrBot插件，当好友购买新游戏时会自动发送通知。

## 功能特性

- 🎮 监控Steam好友游戏库变动
- 🔔 新游戏购买自动通知
- 📊 查看好友游戏库统计
- ⏰ 定时轮询检查
- 🎯 支持多个好友同时监控

## 安装

1. 将插件文件夹放入AstrBot的 `data/plugins/` 目录
2. 重启AstrBot或在WebUI中加载插件

## 配置

在AstrBot WebUI的插件配置中设置：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `steam_api_key` | Steam Web API Key | 无（必填） |
| `poll_interval` | 轮询间隔（分钟） | 30 |
| `notify_group` | 通知发送目标 | 空（当前会话） |
| `enable_notification` | 启用新游戏通知 | true |

### 获取Steam Web API Key

1. 访问 https://steamcommunity.com/dev/apikey
2. 使用Steam账号登录
3. 域名填 `localhost`
4. 同意使用条款
5. 复制生成的API Key

## 命令

### 添加监控好友
```
/steamlib add <steam_id> [昵称]
```

示例：
```
/steamlib add 76561198012345678 小明
```

### 删除监控好友
```
/steamlib del <steam_id>
```

### 查看监控列表
```
/steamlib list
```

### 立即检查游戏库变动
```
/steamlib check [steam_id]
```

- 不指定steam_id：检查所有好友
- 指定steam_id：只检查该好友

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

## 注意事项

- 需要好友的游戏详情设置为"公开"才能获取游戏列表
- Steam API有调用频率限制，建议轮询间隔不低于15分钟
- 插件数据存储在 `data/plugin_data/astrbot_plugin_steam_library_monitor/` 目录

## 依赖

- httpx >= 0.27.0

## 许可证

MIT License
