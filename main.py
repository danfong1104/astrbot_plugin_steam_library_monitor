import asyncio
import json
from pathlib import Path
from typing import Optional

import httpx
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools


class SteamLibraryMonitor(Star):
    """Steam游戏库监控插件，监控好友游戏库变动并通知新购买的游戏。"""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.data_dir: Path = StarTools.get_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Steam API配置
        self.steam_api_key: str = config.get("steam_api_key", "")
        self.poll_interval: int = config.get("poll_interval", 30)
        self.notify_group: str = config.get("notify_group", "")
        self.enable_notification: bool = config.get("enable_notification", True)

        # 数据文件路径
        self.friends_file: Path = self.data_dir / "friends.json"
        self.games_cache_file: Path = self.data_dir / "games_cache.json"

        # 加载数据
        self.friends: dict[str, dict] = self._load_json(self.friends_file, {})
        self.games_cache: dict[str, list[int]] = self._load_json(self.games_cache_file, {})

        # 轮询任务
        self._poll_task: Optional[asyncio.Task] = None
        self._client: Optional[httpx.AsyncClient] = None

        # 启动轮询
        self._start_polling()

    def _load_json(self, path: Path, default):
        """从JSON文件加载数据。"""
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载 {path} 失败: {e}")
        return default

    def _save_json(self, path: Path, data):
        """保存数据到JSON文件。"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存 {path} 失败: {e}")

    def _start_polling(self):
        """启动轮询任务。"""
        if not self.steam_api_key:
            logger.warning("Steam API Key 未配置，轮询任务未启动")
            return

        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info(f"Steam游戏库轮询已启动，间隔 {self.poll_interval} 分钟")

    async def _poll_loop(self):
        """轮询循环。"""
        while True:
            try:
                await self._check_all_friends()
            except Exception as e:
                logger.error(f"轮询检查失败: {e}")
            await asyncio.sleep(self.poll_interval * 60)

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建HTTP客户端。"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _get_owned_games(self, steam_id: str) -> Optional[list[dict]]:
        """获取用户拥有的所有游戏。"""
        client = await self._get_client()
        url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
        params = {
            "key": self.steam_api_key,
            "steamid": steam_id,
            "format": "json",
            "include_appinfo": 1,
            "include_played_free_games": 1,
        }

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("response", {}).get("games", [])
        except Exception as e:
            logger.error(f"获取 {steam_id} 的游戏列表失败: {e}")
            return None

    async def _get_player_summary(self, steam_id: str) -> Optional[dict]:
        """获取玩家基本信息。"""
        client = await self._get_client()
        url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
        params = {
            "key": self.steam_api_key,
            "steamids": steam_id,
            "format": "json",
        }

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            players = data.get("response", {}).get("players", [])
            return players[0] if players else None
        except Exception as e:
            logger.error(f"获取 {steam_id} 的玩家信息失败: {e}")
            return None

    async def _check_friend_games(self, steam_id: str, nickname: str) -> list[dict]:
        """检查单个好友的游戏库变化。"""
        current_games = await self._get_owned_games(steam_id)
        if current_games is None:
            return []

        # 提取当前游戏ID列表
        current_game_ids = {game["appid"] for game in current_games}

        # 获取缓存的游戏ID列表
        cached_game_ids = set(self.games_cache.get(steam_id, []))

        # 如果是首次检查，只保存缓存不通知
        if steam_id not in self.games_cache:
            self.games_cache[steam_id] = list(current_game_ids)
            self._save_json(self.games_cache_file, self.games_cache)
            logger.info(f"首次记录 {nickname} 的游戏库，共 {len(current_game_ids)} 个游戏")
            return []

        # 检测新增游戏
        new_game_ids = current_game_ids - cached_game_ids
        new_games = [g for g in current_games if g["appid"] in new_game_ids]

        # 更新缓存
        if new_games:
            self.games_cache[steam_id] = list(current_game_ids)
            self._save_json(self.games_cache_file, self.games_cache)

        return new_games

    async def _check_all_friends(self):
        """检查所有好友的游戏库变化。"""
        if not self.friends:
            return

        for steam_id, friend_info in list(self.friends.items()):
            nickname = friend_info.get("nickname", steam_id)
            new_games = await self._check_friend_games(steam_id, nickname)

            if new_games and self.enable_notification:
                await self._notify_new_games(nickname, new_games)

    async def _notify_new_games(self, nickname: str, new_games: list[dict]):
        """发送新游戏购买通知。"""
        if not new_games:
            return

        game_names = [g.get("name", "未知游戏") for g in new_games]
        games_text = "\n".join([f"  - {name}" for name in game_names])

        message = f"🎮 Steam好友游戏库更新\n\n👤 {nickname} 购买了新游戏：\n{games_text}"

        if self.notify_group:
            # 发送到指定会话
            try:
                await self.context.send_message(self.notify_group, message)
                logger.info(f"已发送 {nickname} 的新游戏通知到 {self.notify_group}")
            except Exception as e:
                logger.error(f"发送通知失败: {e}")
        else:
            # 如果没有指定通知目标，记录日志
            logger.info(f"{nickname} 购买了新游戏: {', '.join(game_names)}")

    @filter.command_group("steam")
    def steam(self):
        """Steam游戏库监控命令组。"""
        pass

    @steam.command("add", alias={"添加好友"})
    async def add_friend(self, event: AstrMessageEvent, steam_id: str, nickname: str = ""):
        """添加要监控的Steam好友。"""
        if not self.steam_api_key:
            yield event.plain_result("❌ 请先在插件配置中设置 Steam Web API Key")
            return

        # 验证Steam ID格式
        if not steam_id.isdigit() or len(steam_id) < 17:
            yield event.plain_result("❌ 无效的Steam ID格式，Steam ID应为17位数字")
            return

        # 验证Steam ID是否有效
        player_info = await self._get_player_summary(steam_id)
        if not player_info:
            yield event.plain_result("❌ 无法找到该Steam用户，请检查Steam ID是否正确")
            return

        # 使用API返回的昵称或用户指定的昵称
        if not nickname:
            nickname = player_info.get("personaname", steam_id)

        # 添加到监控列表
        self.friends[steam_id] = {
            "nickname": nickname,
            "added_by": event.get_sender_id(),
            "avatar": player_info.get("avatarfull", ""),
        }
        self._save_json(self.friends_file, self.friends)

        # 立即检查一次游戏库
        new_games = await self._check_friend_games(steam_id, nickname)
        game_count = len(self.games_cache.get(steam_id, []))

        result_msg = f"✅ 已添加监控好友: {nickname}\n"
        result_msg += f"📊 当前游戏库: {game_count} 个游戏\n"
        if new_games:
            result_msg += f"🆕 检测到新游戏: {len(new_games)} 个"

        yield event.plain_result(result_msg)

    @steam.command("del", alias={"删除好友"})
    async def del_friend(self, event: AstrMessageEvent, steam_id: str):
        """删除监控的Steam好友。"""
        if steam_id not in self.friends:
            yield event.plain_result(f"❌ 未找到Steam ID: {steam_id}")
            return

        nickname = self.friends[steam_id].get("nickname", steam_id)
        del self.friends[steam_id]
        self._save_json(self.friends_file, self.friends)

        # 清除游戏缓存
        if steam_id in self.games_cache:
            del self.games_cache[steam_id]
            self._save_json(self.games_cache_file, self.games_cache)

        yield event.plain_result(f"✅ 已删除监控好友: {nickname}")

    @steam.command("list", alias={"列表"})
    async def list_friends(self, event: AstrMessageEvent):
        """查看监控的好友列表。"""
        if not self.friends:
            yield event.plain_result("📋 监控列表为空，使用 /steam add <steam_id> 添加好友")
            return

        lines = ["📋 Steam好友监控列表:\n"]
        for steam_id, info in self.friends.items():
            nickname = info.get("nickname", steam_id)
            game_count = len(self.games_cache.get(steam_id, []))
            lines.append(f"  👤 {nickname} (ID: {steam_id})")
            lines.append(f"     📊 游戏数: {game_count}")

        yield event.plain_result("\n".join(lines))

    @steam.command("check", alias={"检查"})
    async def check_now(self, event: AstrMessageEvent, steam_id: str = ""):
        """立即检查游戏库变动。"""
        if not self.steam_api_key:
            yield event.plain_result("❌ 请先在插件配置中设置 Steam Web API Key")
            return

        if not self.friends:
            yield event.plain_result("📋 监控列表为空")
            return

        yield event.plain_result("🔄 正在检查游戏库变动...")

        if steam_id:
            # 检查指定好友
            if steam_id not in self.friends:
                yield event.plain_result(f"❌ 未找到Steam ID: {steam_id}")
                return

            nickname = self.friends[steam_id].get("nickname", steam_id)
            new_games = await self._check_friend_games(steam_id, nickname)
            if new_games:
                game_names = [g.get("name", "未知游戏") for g in new_games]
                yield event.plain_result(f"🆕 {nickname} 新增游戏:\n" + "\n".join([f"  - {n}" for n in game_names]))
            else:
                yield event.plain_result(f"✅ {nickname} 暂无新增游戏")
        else:
            # 检查所有好友
            total_new = 0
            results = []
            for sid, info in self.friends.items():
                nickname = info.get("nickname", sid)
                new_games = await self._check_friend_games(sid, nickname)
                if new_games:
                    total_new += len(new_games)
                    game_names = [g.get("name", "未知游戏") for g in new_games]
                    results.append(f"👤 {nickname}:\n" + "\n".join([f"  - {n}" for n in game_names]))

            if results:
                yield event.plain_result(f"🆕 检测到 {total_new} 个新游戏:\n\n" + "\n\n".join(results))
            else:
                yield event.plain_result("✅ 所有好友暂无新增游戏")

    @steam.command("info", alias={"信息"})
    async def friend_info(self, event: AstrMessageEvent, steam_id: str):
        """查看好友详细信息。"""
        if steam_id not in self.friends:
            yield event.plain_result(f"❌ 未找到Steam ID: {steam_id}")
            return

        friend = self.friends[steam_id]
        nickname = friend.get("nickname", steam_id)
        game_count = len(self.games_cache.get(steam_id, []))

        # 获取玩家在线状态
        player_info = await self._get_player_summary(steam_id)
        status = "未知"
        if player_info:
            state = player_info.get("personastate", 0)
            status_map = {0: "离线", 1: "在线", 2: "忙碌", 3: "离开", 4: "打盹", 5: "想交易", 6: "想玩"}
            status = status_map.get(state, "未知")

        lines = [
            f"👤 好友信息: {nickname}",
            f"🆔 Steam ID: {steam_id}",
            f"🟢 状态: {status}",
            f"📊 游戏数: {game_count}",
            f"📅 添加时间: {friend.get('added_by', '未知')}",
        ]

        yield event.plain_result("\n".join(lines))

    @steam.command("help", alias={"帮助"})
    async def help(self, event: AstrMessageEvent):
        """显示帮助信息。"""
        help_text = """🎮 Steam游戏库监控插件

📌 命令列表:
  /steam add <steam_id> [昵称] - 添加监控好友
  /steam del <steam_id> - 删除监控好友
  /steam list - 查看监控列表
  /steam check [steam_id] - 立即检查游戏库变动
  /steam info <steam_id> - 查看好友详细信息
  /steam help - 显示此帮助

💡 使用说明:
1. 先在插件配置中设置 Steam Web API Key
2. 使用 /steam add 命令添加要监控的好友
3. 插件会自动定期检查游戏库变动
4. 当好友购买新游戏时会收到通知

🔗 获取Steam Web API Key:
https://steamcommunity.com/dev/apikey"""
        yield event.plain_result(help_text)

    @filter.on_astrbot_loaded()
    async def on_loaded(self):
        """AstrBot加载完成后的回调。"""
        logger.info("Steam游戏库监控插件已加载")

    async def terminate(self):
        """插件卸载时的清理工作。"""
        # 取消轮询任务
        if self._poll_task and not self._poll_task.done():
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass

        # 关闭HTTP客户端
        if self._client and not self._client.is_closed:
            await self._client.aclose()

        logger.info("Steam游戏库监控插件已卸载")
