"""Middleware exports for agents_v2."""

from gms.ai.agents_v2.middleware.goal import (
    Goal,
    GoalMiddleware,
    GoalState,
    GoalStatus,
    goals_reducer,
    GOALS_PARTS_KEY,
)
from gms.ai.agents_v2.middleware.kb_search import KBSearchMiddleware
from gms.ai.agents_v2.middleware.steps import (
    STEPS_PARTS_KEY,
    BrowseKBSource,
    BrowseKBStep,
    Replace,
    SearchKBStep,
    Step,
    StepProgress,
    StepsMiddleware,
    StepsState,
    steps_reducer,
)
from gms.ai.agents_v2.middleware.title_generation import TitleGenerationMiddleware
from gms.ai.agents_v2.middleware.data_overview import DataOverviewMiddleware
from gms.ai.agents_v2.middleware.file_upload import FileUploadMiddleware
from gms.ai.agents_v2.middleware.state_sync import (
    EndStateNotifierMiddleware,
    StartStateNotifierMiddleware,
)
from gms.ai.agents_v2.middleware.task import (
    TASK_PARTS_KEY,
    TaskMiddleware,
)

__all__ = [
    # Goal
    "Goal",
    "GoalMiddleware",
    "GoalState",
    "GoalStatus",
    "goals_reducer",
    "GOALS_PARTS_KEY",
    # Steps
    "STEPS_PARTS_KEY",
    "Replace",
    "BrowseKBSource",
    "BrowseKBStep",
    "SearchKBStep",
    "Step",
    "StepProgress",
    "StepsMiddleware",
    "StepsState",
    "steps_reducer",
    # Other middleware
    "KBSearchMiddleware",
    "TitleGenerationMiddleware",
    "DataOverviewMiddleware",
    "FileUploadMiddleware",
    "StartStateNotifierMiddleware",
    "EndStateNotifierMiddleware",
    # Task
    "TASK_PARTS_KEY",
    "TaskMiddleware",
]
