# Steam游戏库监控插件

一个用于监控Steam好友游戏库变动的AstrBot插件，当好友购买新游戏时会自动发送通知，支持图片渲染、游戏价格查询和史低信息。

## 功能特性

- 🎮 监控Steam好友游戏库变动
- 🔔 新游戏购买自动通知
- 🖼️ 图文混合消息推送（文字+图片一条消息）
- 💰 游戏价格查询（ITAD API获取当前售价和史低）
- 🏷️ 购买评价（根据当前价格与史低比较）
- ⏰ 定时轮询检查
- 🎯 支持多个好友同时监控
- 📱 支持多群推送
- ✨ 自定义消息模板和购买评价

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
| `itad_api_key` | ITAD API Key（用于获取史低价格） | 空 |
| `sgdb_api_key` | SteamGridDB API Key（用于获取游戏封面） | 空 |
| `notify_groups` | 推送通知的群号列表 | 空 |
| `message_template` | 自定义消息模板 | `恭喜 {username} 新入库了 {gamename}` |
| `show_game_info` | 显示游戏资讯（价格、链接等） | true |
| `comment_at_lowest` | 价格≤史低时的购买评价 | `绝佳的买入时机，薅羊毛小能手！` |
| `comment_above_lowest` | 价格>史低时的购买评价 | `有点冤大头了呢！为什么不再等等。` |
| `poll_interval` | 轮询间隔（分钟） | 30 |
| `enable_notification` | 启用新游戏通知 | true |
| `render_image` | 启用图片渲染通知 | true |

### 配置示例

**steam_ids**（文本框，每行一个）：
```
76561198203485468:小明
76561198012345678:小红
76561198098765432
```

格式：`Steam ID:昵称`（昵称可选，用英文冒号分隔）

**notify_groups**（文本框，每行一个群号）：
```
123456789
987654321
```

**message_template**（消息模板）：
```
恭喜 {username} 新入库了 {gamename}
```

可用变量：
- `{username}` - 用户名
- `{gamename}` - 游戏名

### 获取API Key

1. **Steam Web API Key**（必填）：
   - 访问 https://steamcommunity.com/dev/apikey
   - 使用Steam账号登录
   - 域名填 `localhost`
   - 同意使用条款
   - 复制生成的API Key

2. **ITAD API Key**（推荐，用于获取史低价格）：
   - 访问 https://isthereanydeal.com/apps/
   - 注册账号并登录
   - 创建应用获取API Key

3. **SteamGridDB API Key**（可选，用于获取游戏封面）：
   - 访问 https://www.steamgriddb.com/profile/preferences/api
   - 注册账号并登录
   - 复制API Key

## 命令

### 测试推送效果
```
/steamlib test
```

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

## 实现原理

### 1. 游戏库监控

插件通过Steam Web API的 `IPlayerService/GetOwnedGames/v1` 接口获取用户的游戏列表，然后与本地缓存进行比对，检测新增游戏。

### 2. 价格查询

- **ITAD API**：优先使用 IsThereAnyDeal API 获取游戏的当前国区售价和历史最低价
- **Steam API**：作为备用方案，使用Steam官方API获取当前价格（无史低信息）

### 3. 图片渲染

使用Pillow库渲染游戏封面图、玩家头像和购买信息，生成精美的通知图片。

### 4. 消息推送

使用AstrBot的 `MessageChain` 组件，将文字和图片组合成一条消息发送，确保图文并茂的展示效果。

## 通知效果示例

```
🎮 恭喜 小明 新入库了 Mirror 2: Project X
💰 当前国区售价: ¥37.00
📉 原价: ¥110.00 (-66%)
🏷️ 史低售价: ¥37.00
📝 购买评价: 绝佳的买入时机，薅羊毛小能手！
🔗 Steam商店: https://store.steampowered.com/app/123456

[游戏封面图片]
```

## 购买评价逻辑

- 当 **当前价格 ≤ 史低** 时：显示 `comment_at_lowest`（默认：绝佳的买入时机，薅羊毛小能手！）
- 当 **当前价格 > 史低** 时：显示 `comment_above_lowest`（默认：有点冤大头了呢！为什么不再等等。）

购买评价可在配置页自定义修改。

## 后台日志

插件启动时会输出详细的配置信息：

```
==================================================
[Steam游戏库监控] 插件启动中...
[Steam游戏库监控] 监控用户列表 (2 人):
  1. 小明 (ID: 76561198203485468)
  2. 小红 (ID: 76561198012345678)
[Steam游戏库监控] 推送群号列表 (1 个):
  - 群 123456789
[Steam游戏库监控] 轮询间隔: 30 分钟
[Steam游戏库监控] 图片渲染: 启用
[Steam游戏库监控] 通知推送: 启用
[Steam游戏库监控] ITAD API: 已配置
==================================================
[Steam游戏库监控] 轮询任务已启动
```

每次轮询时：

```
[Steam游戏库监控] 开始轮询检查 - 2026-06-05 15:30:00
[Steam游戏库监控] 正在检查 2 个用户...
[Steam游戏库监控] 轮询检查完成
[Steam游戏库监控] 下次轮询时间: 2026-06-05 16:00:00
```

## 注意事项

- 需要好友的游戏详情设置为"公开"才能获取游戏列表
- Steam API有调用频率限制，建议轮询间隔不低于15分钟
- 配置ITAD API Key可获取史低价格信息，否则只显示当前价格
- 插件数据存储在 `data/plugin_data/astrbot_plugin_steam_library_monitor/` 目录

## 依赖

- httpx >= 0.27.0
- Pillow >= 10.0.0

## 许可证

MIT License

---

## 致谢

特别感谢 [Maoer233](https://github.com/Maoer233) 大佬的技术参考和优秀插件！

### 推荐插件

#### Maoer233 的 Steam 插件

- **Steam游戏价格史低查询插件**
  - 仓库：https://github.com/Maoer233/astrbot_plugins_steam_shop_price
  - 功能：查询Steam游戏的当前价格、史低价格、多区比价

- **Steam好友状态监控插件**
  - 仓库：https://github.com/Maoer233/astrbot_plugin_steam_status_monitor
  - 功能：监控Steam好友在线状态、正在游玩的游戏、成就获取

#### danfong1104 的其他 Steam 插件

- **Steam每日热销插件**
  - 仓库：https://github.com/danfong1104/astrbot_plugin_steam_topsellers
  - 功能：每日推送Steam热销游戏榜单

- **Steam Mod监控插件**
  - 仓库：https://github.com/danfong1104/astrbot_plugin_steammod_monitor
  - 功能：监控Steam创意工坊Mod更新

#### 更多插件

访问作者主页查看更多插件：https://github.com/danfong1104
