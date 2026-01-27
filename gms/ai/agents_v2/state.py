from pydantic import BaseModel, Field, PrivateAttr
from typing import Literal, Any, AsyncIterator
from dataclasses import dataclass, field
from anyio import create_memory_object_stream
import json

######### UTILS
import jsonpatch

BlockType = Literal["PLAN", "STEP", "ASK_TEXT"]


class Block(BaseModel):
    class Content(BaseModel):
        pass

    usage: BlockType
    _previous: dict = PrivateAttr(default={})

    def diff(self):
        model_dump = self.model_dump(exclude=["usage"])

        diffs = []
        for k, v in model_dump.items():
            prev = self._previous.get(k)
            patch = jsonpatch.make_patch(prev, v)
            self._previous[k] = v
            if len(patch.patch):
                diffs.append(
                    {"usage": self.usage, "diff": {"field": k, "patches": patch.patch}}
                )

        return diffs


class Source(BaseModel):
    name: str
    snippet: str
    metadata: dict[str, Any] | None = None
    is_from_kb: bool = Field(default=False)


class SearchQuery(BaseModel):
    query: str
    limit: int


######### PLAN #########


class Goal(BaseModel):
    id: str
    description: str
    final: bool
    pass


class PlanBlockContent(Block.Content):
    goals: list[Goal] = Field(default_factory=list)

    def get_content_fields(self):
        return {"goals": self.goals}


class PlanBlock(Block):
    usage: Literal["PLAN"] = "PLAN"
    plan_content: PlanBlockContent = Field(default_factory=PlanBlockContent)

    def add_goal(self, goal: str):
        goal_id = len(self.plan_content.goals)
        self.plan_content.goals.append(Goal(id=str(goal_id), description=goal))


######### PLAN #########


######### STEP #########
class IntialQueryStep(BaseModel):
    class Content(BaseModel):
        query: str

    id: str = ""
    type: Literal["INITIAL_QUERY"] = "INITIAL_QUERY"
    intial_query: Content


class KBSearchStep(BaseModel):
    class Content(BaseModel):
        goal_id: str
        queries: list[SearchQuery]

    id: str
    type: Literal["KB_SEARCH"] = "KB_SEARCH"
    kb_search: Content


class BrowseKBResultStep(BaseModel):
    class Content(BaseModel):
        goal_id: str
        kb_result: list[Source]

    id: str
    type: Literal["BROWSE_KB_RESULT"] = "BROWSE_KB_RESULT"
    browse_kb_result: Content


Steps = IntialQueryStep | KBSearchStep | BrowseKBResultStep


class StepBlockContent(Block.Content):
    steps: list[Steps] = Field(default_factory=list)
    progress: Literal["DEFAULT", "IN_PROGRESS", "DONE", "ERROR"] = Field(
        default="DEFAULT"
    )
    final: bool = False


class StepBlock(Block):
    usage: Literal["STEP"] = "STEP"
    step_content: StepBlockContent = Field(default_factory=StepBlockContent)

    def add_step(self, step: Steps):
        steps = self.step_content.steps
        steps.append(step)
        self.step_content.steps = steps

    def add_intial_query_step(self, query: str):
        intial_query_step = IntialQueryStep(
            intial_query=IntialQueryStep.Content(query=query),
        )
        self.add_step(intial_query_step)

    def add_kb_search_step(self, goal_id: str, id: str, queries: list[str], limit: int):
        queries = [SearchQuery(query=q, limit=limit) for q in queries]
        search_kb_step = KBSearchStep(
            id=id,
            kb_search=KBSearchStep.Content(queries=queries, goal_id=goal_id),
        )
        self.add_step(search_kb_step)

    def add_browse_kb_result_step(self, goal_id: str, id: str, results: list[Source]):
        search_kb_result_step = BrowseKBResultStep(
            id=id,
            kb_result_content=BrowseKBResultStep.Content(
                kb_result=results, goal_id=goal_id
            ),
        )
        self.add_step(search_kb_result_step)


######### STEP #########


######### ASK TEXT RESULT #########
class MarkdownBlockContent(Block.Content):
    progress: Literal["DEFAULT", "IN_PROGRESS", "DONE", "ERROR"] = "DEFAULT"
    chunks: list[str] = Field(default_factory=list)
    chunk_starting_offset: int = Field(default=0)
    answer: str | None = None


class AskResultBlock(Block):
    answer_markdown_content: MarkdownBlockContent = Field(
        default_factory=MarkdownBlockContent
    )


######### ASK TEXT RESULT #########


######### ANSWER SOURCE #########
class AnswerSourceContent(BaseModel):
    sources: list[Source] = Field(default_factory=[])


class AnswerSourceBlock(Block):
    usage: Literal["PLAN"] = "PLAN"
    answer_source_content: AnswerSourceContent


######### ANSWER SOURCE #########


class AgentRunState(BaseModel):
    blocks: list[Block] = Field(default_factory=list)

    def step(self) -> StepBlock:
        for b in self.blocks:
            if b.usage == "STEP":
                return b
        block = StepBlock()
        self.blocks.append(block)
        return block

    def plan(self) -> PlanBlock:
        for b in self.blocks:
            if b.usage == "PLAN":
                return b
        block = PlanBlock()
        self.blocks.append(block)
        return block

    def ask_result(self) -> AskResultBlock:
        for b in self.blocks:
            if b.usage == "ASK_TEXT":
                return b
        block = AskResultBlock()
        self.blocks.append(block)
        return block


@dataclass
class AgentContext:
    state = AgentRunState()
    sender = None
    receiver = None

    async def notify_start(self):
        # await self.sender.send("start")
        print("Sent")

    async def notify_end(self):
        await self.sender.send("end")

    async def notify_block_changes(self):
        diff = [d for b in self.state.blocks for d in b.diff()]
        if len(diff) == 0:
            return

        await self.sender.send_nowait(json.dumps({"diff": diff}))

    async def get_response(self) -> AsyncIterator[str]:
        sender, receiver = create_memory_object_stream()
        self.sender = sender

        try:
            async with receiver:
                async for event in receiver:
                    yield f"data: {event}\n\n"
        except Exception as e:
            print(e)
            raise

    def close(self):
        self.receiver.close()
        self.sender.close()
