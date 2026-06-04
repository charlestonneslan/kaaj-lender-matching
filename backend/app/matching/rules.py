from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

NUMERIC_OPS = {"gte", "lte", "gt", "lt", "eq", "between"}
SET_OPS = {"in", "not_in"}
BOOLEAN_OPS = {"eq"}
COMPOSITE_OPS = {"call"}


class RuleSpec(BaseModel):
    kind: str = Field(description="numeric | set | boolean | composite")
    field: str
    op: str
    value: Any
    weight: int = 1
    hard: bool = True
    message: str | None = None


@dataclass
class EvalOutcome:
    passed: bool
    actual: Any
    required: Any
    message: str


def get_field(application: dict, path: str) -> Any:
    cur: Any = application
    for part in path.split("."):
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
    return cur


def _fmt(template: str | None, actual: Any, required: Any, field: str, op: str) -> str:
    if template:
        try:
            return template.format(actual=actual, required=required, field=field, op=op)
        except (KeyError, IndexError):
            return template
    return f"{field} {op} {required} (got {actual})"


def _eval_numeric(actual: Any, op: str, required: Any) -> bool:
    if actual is None:
        return False
    if op == "gte":
        return actual >= required
    if op == "lte":
        return actual <= required
    if op == "gt":
        return actual > required
    if op == "lt":
        return actual < required
    if op == "eq":
        return actual == required
    if op == "between":
        lo, hi = required
        return lo <= actual <= hi
    raise ValueError(f"unsupported numeric op: {op}")


def _eval_set(actual: Any, op: str, required: Any) -> bool:
    members = {str(v).lower() for v in required}
    val = str(actual).lower() if actual is not None else ""
    if op == "in":
        return val in members
    if op == "not_in":
        return val not in members
    raise ValueError(f"unsupported set op: {op}")


def _eval_boolean(actual: Any, op: str, required: Any) -> bool:
    actual_bool = bool(actual) if actual is not None else False
    if op == "eq":
        return actual_bool == bool(required)
    raise ValueError(f"unsupported boolean op: {op}")


COMPOSITE_REGISTRY: dict[str, Any] = {}


def register_composite(name: str):
    def deco(fn):
        COMPOSITE_REGISTRY[name] = fn
        return fn
    return deco


@register_composite("comp_credit_pct")
def _comp_credit_pct(app: dict, required: float) -> tuple[bool, Any]:
    pct = get_field(app, "business_credit.comparable_credit_pct") or 0
    return pct >= required, pct


@register_composite("revolver_limit")
def _revolver_limit(app: dict, _required: Any) -> tuple[bool, Any]:
    rev = get_field(app, "guarantor.revolving_balance") or 0
    uns = get_field(app, "guarantor.unsecured_debt") or 0
    over_rev = rev > 30000
    over_combined = (rev + uns) > 50000
    return not (over_rev or over_combined), {"revolving": rev, "combined": rev + uns}


@register_composite("bk_compliant")
def _bk_compliant(app: dict, required_years: float) -> tuple[bool, Any]:
    g = get_field(app, "guarantor")
    has_bk = _attr(g, "has_bankruptcy", False)
    if not has_bk:
        return True, "no bankruptcy on file"
    yrs = _attr(g, "bk_discharge_years", None)
    if yrs is None:
        return False, "bankruptcy on file with no discharge date"
    return yrs >= required_years, yrs


def _attr(obj: Any, key: str, default: Any) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


@register_composite("clean_credit_history")
def _clean_credit_history(app: dict, _required: Any) -> tuple[bool, Any]:
    g = get_field(app, "guarantor")
    checks = ["has_judgments", "has_foreclosure", "has_repossession", "has_tax_lien", "has_recent_collections"]
    hits = [name.replace("has_", "") for name in checks if _attr(g, name, False)]
    return len(hits) == 0, hits


def evaluate_rule(rule: RuleSpec, application: dict) -> EvalOutcome:
    field = rule.field
    op = rule.op
    required = rule.value
    actual = get_field(application, field)

    if rule.kind == "numeric":
        passed = _eval_numeric(actual, op, required)
    elif rule.kind == "set":
        passed = _eval_set(actual, op, required)
    elif rule.kind == "boolean":
        passed = _eval_boolean(actual, op, required)
    elif rule.kind == "composite":
        fn = COMPOSITE_REGISTRY.get(field)
        if fn is None:
            raise ValueError(f"unknown composite: {field}")
        passed, actual = fn(application, required)
    else:
        raise ValueError(f"unknown rule kind: {rule.kind}")

    message = _fmt(rule.message, actual, required, field, op)
    return EvalOutcome(passed=passed, actual=actual, required=required, message=message)
