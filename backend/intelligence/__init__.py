"""
intelligence package — Generic Hybrid Academic Data Intelligence Engine.
"""

from .schema import AcademicSchema
from .engine import AcademicQueryEngine, QueryPlan, QueryResult
from .memory import ConversationMemory
from .planner import QueryPlanner
from .dispatcher import HybridIntelligenceDispatcher

__all__ = [
    "AcademicSchema",
    "AcademicQueryEngine",
    "QueryPlan",
    "QueryResult",
    "ConversationMemory",
    "QueryPlanner",
    "HybridIntelligenceDispatcher",
]
