from typing import List, Literal, Optional
from agentscope import agent
from pydantic import BaseModel, Field


class DiscussionModel(BaseModel):
    reach_agreement: bool = Field(description="是否达成一致意见")
    confidence_level: int = Field(
        description="对当前推理的信心程度(0-1)，0-1", ge=0, le=1
    )
    key_evidence: Optional[str] = Field(
        description="支持你观点的关键证据", default=None
    )


class WerewolfKillModel(BaseModel):
    target: str = Field(description="要击杀玩家姓名")
    kill_strategy: str = Field(description="击杀策略说明")
    team_coordination: Optional[str] = Field(
        description="与狼队友的配合计划", default=None
    )


class WitchModel(BaseModel):
    use_antidote: bool = Field(description="是否使用解药救人", default=False)
    use_poison: bool = Field(description="是否使用毒药杀人", default=False)
    target_name: Optional[str] = Field(
        description="目标玩家姓名（救人或毒杀的对象）", default=None
    )
    action_reason: Optional[str] = Field(description="行动理由", default=None)


def get_seer_model(agents: List[agent.Agent]) -> type[BaseModel]:
    class SeerModel(BaseModel):
        target: Literal[tuple(_.name for _ in agents)] = Field(
            description="要查验玩家姓名"
        )
        check_reason: str = Field(description="查验理由")
        priority_level: int = Field(description="查验优先级(0-1)", ge=0, le=1)

    return SeerModel


def get_vote_model(agents: List[agent.Agent]) -> type[BaseModel]:
    class VoteModel(BaseModel):
        target: Literal[tuple(_.name for _ in agents)] = Field(
            description="要投票玩家姓名"
        )
        vote_reason: str = Field(description="投票理由")
        confidence_level: int = Field(
            description="对当前投票的信心程度(0-1)", ge=0, le=1
        )

    return VoteModel


def get_hunter_model(agents: List[agent.Agent]) -> type[BaseModel]:
    class HunterModel(BaseModel):
        target: Literal[tuple(_.name for _ in agents)] = Field(
            description="要击杀玩家姓名"
        )
        kill_reason: str = Field(description="击杀理由")
        confidence_level: int = Field(
            description="对当前击杀的信心程度(0-1)", ge=0, le=1
        )

    return HunterModel
