from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from ..services.snowflake_client import (
    get_all_strategies,
    get_audit_history,
    get_leaderboard,
    get_audit_by_id,
)
from ..services.backboard_client import (
    push_strategy_summary,
    push_leaderboard as push_leaderboard_to_backboard,
)

router = APIRouter(prefix="/strategies", tags=["strategies"])


class CompareRequest(BaseModel):
    strategy_names: list[str]


@router.get("/")
def list_strategies(background_tasks: BackgroundTasks):
    """List all audited strategies with latest scores."""
    strategies = get_all_strategies()
    # Push to Backboard in background for dashboard sync
    if strategies:
        background_tasks.add_task(push_strategy_summary, strategies)
    return {"strategies": strategies}


@router.get("/leaderboard")
def leaderboard(background_tasks: BackgroundTasks, limit: int = 20):
    """Top strategies by Edge Score."""
    results = get_leaderboard(limit=limit)
    # Push to Backboard in background for dashboard sync
    if results:
        background_tasks.add_task(push_leaderboard_to_backboard, results)
    return {"strategies": results}


@router.get("/{strategy_name}/history")
def strategy_history(strategy_name: str, limit: int = 10):
    """Audit history for a strategy."""
    audits = get_audit_history(strategy_name, limit=limit)
    return {"strategy_name": strategy_name, "audits": audits}


@router.post("/compare")
def compare_strategies(body: CompareRequest):
    """Side-by-side comparison of strategies (latest audit each)."""
    results = []
    for name in body.strategy_names[:2]:
        history = get_audit_history(name, limit=1)
        if history:
            audit = get_audit_by_id(history[0].get("AUDIT_ID", ""))
            results.append(audit)
        else:
            results.append(None)

    return {"comparison": results}
