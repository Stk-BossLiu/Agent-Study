import json
import os
from random import Random

from agentscope import agent, formatter
from typing import Dict, List

from agentscope.credential import OpenAICredential
from agentscope.event import EventType
from agentscope.message import Msg, TextBlock, UserMsg
from agentscope.model import OpenAIChatModel


from structured_output import (
    DiscussionModel,
    WerewolfKillModel,
    WitchModel,
    get_hunter_model,
    get_seer_model,
    get_vote_model,
)
from utils import MAX_DISCUSSION_ROUND, MAX_GAME_ROUND, format_player_list
from game_roles import GameRoles
from game_hoster import GameHoster
from prompt import ChinesePrompts
from dotenv import load_dotenv

load_dotenv()


class ThreeKingdomsWerewolfGame:
    def __init__(self):
        self.players: Dict[str, agent.Agent] = {}
        self.roles: Dict[str, str] = {}
        self.alive_players: List[agent.Agent] = []
        self.villagers: List[agent.Agent] = []  # 村民
        self.werewolves: List[agent.Agent] = []  # 狼人
        self.seers: List[agent.Agent] = []  # 预言家
        self.witches: List[agent.Agent] = []  # 女巫
        self.hunters: List[agent.Agent] = []  # 猎人
        self.game_hoster = GameHoster()  # 游戏主持人
        pass

        """
        添加玩家
        @param role: 扮演角色 女巫，猎人，预言家，狼人，村民
        @param character: 角色描述
        @return: 玩家代理
        """

    async def add_player(self, role: str, character: str) -> agent.Agent:
        self.roles[character] = role
        _agent = agent.Agent(
            name=character,
            system_prompt=ChinesePrompts.get_role_prompt(role, character),
            model=OpenAIChatModel(
                credential=OpenAICredential(
                    api_key=os.getenv("LLM_API_KEY"), base_url=os.getenv("LLM_BASE_URL")
                ),
                model=os.getenv("LLM_MODEL_ID"),
            ),
        )
        await _agent.observe(
            await self.game_hoster.announce(
                f"【{character}】你在这场三国狼人杀中扮演{GameRoles.get_role_desc(role)}，"
                f"你的角色是{character}。{GameRoles.get_role_ability(role)}"
            )
        )
        self.players[character] = _agent
        self.alive_players.append(_agent)
        # msg = await _agent.reply(
        #     inputs=UserMsg(
        #         name="user",
        #         content="在key_evidence里回复你叫什么名字，扮演什么角色+已准备就绪",
        #     )
        # )
        # print("🙋" + json.loads(msg.get_text_content()).get("key_evidence"))

        return _agent

    async def setup_game(self, player_count: int = 6):
        roles = GameRoles.get_standard_setup(player_count)
        characters: List[str] = Random().sample(
            [
                "刘备",
                "关羽",
                "张飞",
                "诸葛亮",
                "赵云",
                "曹操",
                "司马懿",
                "周瑜",
                "孙权",
            ],
            player_count,
        )
        for i, (role, character) in enumerate(zip(roles, characters)):
            _agent = await self.add_player(role, character)
            if role == "狼人":
                self.werewolves.append(_agent)
            elif role == "预言家":
                self.seers.append(_agent)
            elif role == "女巫":
                self.witches.append(_agent)
            elif role == "猎人":
                self.hunters.append(_agent)
            else:
                self.villagers.append(_agent)

        await self.game_hoster.announce(
            f"三国狼人杀游戏开始！参与者：{format_player_list(self.alive_players)}"
        )
        print(f"✅ 游戏设置完成，共{len(self.alive_players)}名玩家")

    """
    狼人阶段
    @param round: 轮次
    @return: 狼人阶段结果
    """

    async def werewolf_phase(self, round: int):
        if not self.werewolves:
            return None
        await self.game_hoster.announce(f"🐺 狼人请睁眼, 选择今晚要击杀的目标。。。")
        msg_contents = []

        kill_votes = []
        print("===============狼人讨论开始==============")
        for _ in range(MAX_DISCUSSION_ROUND):
            for werewolf in self.werewolves:
                msg = await self.game_hoster.announce(
                    f"狼人们，请讨论今晚的击杀目标。"
                    f"现在是第{round}轮游戏，游戏总轮数为{MAX_GAME_ROUND}轮"
                    f"现存狼人：{format_player_list(self.werewolves)}"
                    f"存活玩家：{format_player_list(self.alive_players)}"
                    f"讨论历史：{'\n'.join(msg_contents)}",
                    False,
                )
                result = await werewolf.reply(
                    inputs=msg, structured_schema=DiscussionModel
                )
                data = result.structured_output
                text = f"【{werewolf.name}】:{data["key_evidence"]}"
                print(text)
                msg_contents.append(text)
        print("===============狼人讨论结束==============")
        print("===============狼人投票开始==============")
        kill_votes = []
        for werewolf in self.werewolves:
            msg = await self.game_hoster.announce(
                f"狼人们，请选择今晚的击杀目标。", False
            )
            result = await werewolf.reply(
                inputs=msg, structured_schema=WerewolfKillModel
            )
            data = result.structured_output
            print(f"🐺{werewolf.name}:{data}")
            kill_votes.append(data)
        print("===============狼人投票结束==============")
        # 处理投票结果
        killed_players = []
        for i, vote_msg in enumerate(kill_votes):
            if vote_msg is None:
                continue
            target = vote_msg.get("target")
            if target and target not in killed_players:
                killed_players.append(vote_msg.get("target"))

        msg = await self.game_hoster.announce(
            f"第{round}轮狼人行动信息:"
            f"击杀玩家: {",".join(killed_players)}"
            f"讨论历史: {'\n'.join(msg_contents)}",
            False,
        )
        for werewolf in self.werewolves:
            await werewolf.observe(msg)
        print("===============狼人阶段结束==============")
        print(f"第{round}轮狼人行动信息: 击杀玩家: {killed_players}")
        return killed_players[0] if len(killed_players) > 0 else None

    """
    预言家阶段
    @param round: 轮次
    @return: 预言家阶段结果
    """

    async def seer_phase(self, round: int):
        if not self.seers:
            return None
        seer_agent = self.seers[0]  # 设定只有一名预言家
        await self.game_hoster.announce(f"🔮 预言家请睁眼...")
        msg = await self.game_hoster.announce(
            f"预言家请根据以下信息决定今晚的行动:"
            f"当前游戏轮次: {round}"
            f"存活玩家: {format_player_list(self.alive_players)}"
        )
        seer_action_msg = await seer_agent.reply(
            inputs=msg, structured_schema=get_seer_model(self.alive_players)
        )
        data = seer_action_msg.structured_output
        print(f"🔮{seer_agent.name}:{data}")
        if data is not None and hasattr(data, "target"):
            target_player = data.target
            target_role = self.roles.get(target_player, "村民")
            msg = await self.game_hoster.announce(
                f"在第{round}轮游戏中，你查验了{target_player}，他的角色是{'狼人' if target_role == '狼人' else '好人'}",
                False,
            )
            await seer_agent.observe(msg)

    """
    女巫阶段
    @param round: 轮次
    @return: 女巫阶段结果
    """

    async def witch_phase(self, round: int, death_player: str):
        if not self.witches:
            return None, None
        witch_agent = self.witches[0]  # 设定只有一名女巫
        await self.game_hoster.announce(f"🧙‍♀️ 女巫请睁眼...")

        death_info = (
            f"今晚{death_player}被狼人击杀"
            if death_player is not None
            else "今晚平安无事"
        )
        msg = await self.game_hoster.announce(
            "女巫请根据以下信息决定今晚的行动:"
            f"\n死亡信息: {death_info}"
            f"\n当前游戏轮次: {round}"
        )
        witch_action_msg = await witch_agent.reply(
            inputs=msg, structured_schema=WitchModel
        )
        action_data = witch_action_msg.structured_output
        print(f"🧙‍♀️{witch_agent.name}:{action_data}")
        saved_player = None
        poisoned_player = None

        if action_data is not None and action_data["use_antidote"]:
            saved_player = action_data["target_name"]
            msg = await self.game_hoster.announce(
                f"在第{round}轮游戏中，你使用解药救了{saved_player}"
            )
            await witch_agent.observe(msg)

        if action_data is not None and action_data["use_poison"]:
            poisoned_player = action_data["target_name"]
            msg = await self.game_hoster.announce(
                f"在第{round}轮游戏中，你使用毒药毒杀了{poisoned_player}"
            )
            await witch_agent.observe(msg)
        final_killed = death_player if not saved_player else None
        return final_killed, poisoned_player

    """
    猎人阶段
    @param round: 轮次
    @return: 猎人阶段结果
    """

    async def hunter_phase(self, round: int, voted_out: str):
        if not self.hunters:
            return None
        hunter_agent = self.hunters[0]  # 设定只有一名猎人
        msg = await self.game_hoster.announce(
            f"猎人请根据以下信息决定今晚的行动:"
            f"当前游戏轮次: {round}"
            f"存活玩家: {format_player_list(self.alive_players)}"
            f"大家均认为{voted_out}是狼人",
            False,
        )
        hunter_action_msg = await hunter_agent.reply(
            inputs=msg, structured_schema=get_hunter_model(self.alive_players)
        )
        data = hunter_action_msg.structured_output
        print(f"🏹{hunter_agent.name}:{data}")
        if data is not None and data["target"]:

            if data.get("target"):
                await self.game_hoster.announce(
                    f"在第{round}轮游戏中，猎人击杀了{data.get('target')}"
                )
                return data.get("target")
            else:
                return None
        return None

    def update_alive_players(self, dead_players: List[str]):
        for dead_name in dead_players:
            if dead_name:
                self.alive_players = [
                    p for p in self.alive_players if p.name != dead_name
                ]
                self.werewolves = [p for p in self.werewolves if p.name != dead_name]
                self.seers = [p for p in self.seers if p.name != dead_name]
                self.witches = [p for p in self.witches if p.name != dead_name]
                self.hunters = [p for p in self.hunters if p.name != dead_name]
                self.villagers = [p for p in self.villagers if p.name != dead_name]

    def check_winning(self, alive_players: List[agent.Agent], roles: Dict[str, str]):
        alive_roles = [roles.get(p.name, "村民") for p in alive_players]
        werewolf_count = alive_roles.count("狼人")
        villager_count = len(alive_roles) - werewolf_count
        if werewolf_count == 0:
            return "好人阵营胜利，所有狼人淘汰。"
        elif werewolf_count >= villager_count:
            return "狼人阵营胜利，狼人数量大于等于村民数量。"

        return None

    async def day_phase(self, round: int) -> str:
        await self.game_hoster.day_announcement(round)
        # 讨论阶段
        msg_contents = []
        print("===============讨论阶段开始==============")
        announcement = f"现在是第{round}轮游戏，游戏总轮数为{MAX_GAME_ROUND}轮，开始自由讨论，指出今晚要投票出局的玩家。存活玩家：{format_player_list(self.alive_players)}"
        for player in self.alive_players:
            msg = await self.game_hoster.announce(
                announcement + f"\n讨论历史：{'\n'.join(msg_contents)}", False
            )
            result = await player.reply(inputs=msg, structured_schema=DiscussionModel)
            data = result.structured_output
            text = f"【{player.name}】:{data}"
            print(text)
            msg_contents.append(text)
        print("===============讨论阶段结束==============")
        print("===============投票阶段开始==============")
        vote_info: Dict[str, int] = {
            f"{player.name}": 0 for player in self.alive_players
        }
        votes_history: str = []
        for player in self.alive_players:
            msg = await self.game_hoster.announce(
                f"现在是第{round}轮游戏，游戏总轮数为{MAX_GAME_ROUND}轮, 请投票选择要出局的玩家。"
                f"讨论历史：{'\n'.join(msg_contents)}"
                f"存活玩家：{format_player_list(self.alive_players)}"
                f"当前投票信息：{'\n'.join(votes_history)}",
                False,
            )
            result = await player.reply(
                inputs=msg, structured_schema=get_vote_model(self.alive_players)
            )
            data = result.structured_output

            text = f"【{player.name}】投:{data['target']}, 原因: {data['vote_reason']}"
            print(text)
            vote_info[data["target"]] += 1
            votes_history.append(text)
        print("===============投票阶段结束==============")
        print(f"第{round}轮投票结果: {vote_info}")
        return max(vote_info, key=vote_info.get)

    async def start_game(self):
        try:
            for round in range(1, MAX_GAME_ROUND + 1):
                print(f"🔮 第{round}轮游戏开始")
                # 夜晚阶段
                await self.game_hoster.night_announcement(round)
                # 狼人阶段
                killed_player: str = await self.werewolf_phase(round)

                # 预言家
                await self.seer_phase(round)

                # 女巫
                final_killed, poisoned_player = await self.witch_phase(
                    round, killed_player
                )

                # 更新死亡玩家
                night_deaths = [
                    p for p in [final_killed, poisoned_player] if p is not None
                ]
                self.update_alive_players(night_deaths)

                # 死亡公告
                await self.game_hoster.death_announcement(night_deaths)

                # 检查胜利
                winner = self.check_winning(self.alive_players, self.roles)

                if winner:
                    await self.game_hoster.game_over_announcement(winner)
                    return

                # 白天阶段
                voted_out = await self.day_phase(round)

                hunter_shot = await self.hunter_phase(round, voted_out)

                day_deaths = [p for p in [voted_out, hunter_shot] if p is not None]

                self.update_alive_players(day_deaths)

                winner = self.check_winning(self.alive_players, self.roles)

                if winner:
                    await self.game_hoster.game_over_announcement(winner)
                    return
                print(
                    f"🔮 第{round}轮游戏结束, 存活玩家: {format_player_list(self.alive_players)}"
                )

        except Exception as e:
            print(f"❌ 游戏开始失败: {e}")


if __name__ == "__main__":
    import asyncio

    game = ThreeKingdomsWerewolfGame()
    asyncio.run(game.setup_game(8))
    asyncio.run(game.start_game())
