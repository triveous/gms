"""Middleware exports for agents_v2."""

from gms.ai.agents_v2.middleware.goal import (
    Goal,
    GoalMiddleware,
    GoalState,
    GoalStatus,
    goals_reducer,
)
from gms.ai.agents_v2.middleware.kb_search import KBSearchMiddleware
from gms.ai.agents_v2.middleware.steps import (
    STEPS_PARTS_KEY,
    BrowseKBSource,
    BrowseKBStep,
    SearchKBStep,
    Step,
    StepProgress,
    StepsMiddleware,
    StepsState,
    steps_reducer,
)
from gms.ai.agents_v2.middleware.title_generation import TitleGenerationMiddleware

__all__ = [
    # Goal
    "Goal",
    "GoalMiddleware",
    "GoalState",
    "GoalStatus",
    "goals_reducer",
    # Steps
    "STEPS_PARTS_KEY",
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
]
