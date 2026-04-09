"""Resolve effective Shift for an employee on a calendar date (layered rules)."""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hrm.models import Employee, Shift


def resolve_shift_for_date(employee: Employee, on_date: datetime.date) -> Shift | None:
    """
    Priority:
    1) One-day exception
    2) Date range containing on_date (most recent start_date wins if overlap)
    3) Weekly rule for on_date.weekday() (Mon=0)
    4) Employee.default_shift
    """
    from hrm.models import EmployeeShiftDateRange, EmployeeShiftException, EmployeeShiftWeekday

    ex = (
        EmployeeShiftException.objects.filter(employee=employee, date=on_date)
        .select_related("shift")
        .first()
    )
    if ex:
        return ex.shift

    rng = (
        EmployeeShiftDateRange.objects.filter(
            employee=employee,
            start_date__lte=on_date,
            end_date__gte=on_date,
        )
        .select_related("shift")
        .order_by("-start_date", "-pk")
        .first()
    )
    if rng:
        return rng.shift

    wd = on_date.weekday()
    w = (
        EmployeeShiftWeekday.objects.filter(employee=employee, weekday=wd)
        .select_related("shift")
        .first()
    )
    if w:
        return w.shift

    return employee.default_shift
