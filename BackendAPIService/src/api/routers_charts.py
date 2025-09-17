from datetime import datetime, timedelta
from random import Random
from typing import List

from fastapi import APIRouter, Depends

from .deps import get_current_user
from .schemas import ChartsData, LineChartPoint, PieChartSlice, BarChartBar

router = APIRouter(prefix="/charts", tags=["Charts"])


def _generate_line_series(days: int = 7) -> List[LineChartPoint]:
    rng = Random(42)
    now = datetime.utcnow()
    points: List[LineChartPoint] = []
    base = 100.0
    for i in range(days):
        date = now - timedelta(days=(days - 1 - i))
        base += rng.uniform(-10, 10)
        points.append(LineChartPoint(x=date.strftime("%Y-%m-%d"), y=round(base, 2)))
    return points


def _generate_pie() -> List[PieChartSlice]:
    return [
        PieChartSlice(label="North", value=35),
        PieChartSlice(label="South", value=25),
        PieChartSlice(label="East", value=20),
        PieChartSlice(label="West", value=20),
    ]


def _generate_bar() -> List[BarChartBar]:
    return [
        BarChartBar(label="Q1", value=120),
        BarChartBar(label="Q2", value=150),
        BarChartBar(label="Q3", value=90),
        BarChartBar(label="Q4", value=180),
    ]


@router.get(
    "/data",
    response_model=ChartsData,
    summary="Get chart data",
    description="Provides data sets for Line, Pie, and Bar charts.",
)
# PUBLIC_INTERFACE
def get_charts_data(_=Depends(get_current_user)):
    """Return sample data for multiple chart types."""
    return ChartsData(line=_generate_line_series(), pie=_generate_pie(), bar=_generate_bar())
