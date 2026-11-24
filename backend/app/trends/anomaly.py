
"""
anomaly.py
----------
Statistical anomaly detection for research trends.

Detects:
- Publication volume spikes
- Unusual citation activity
- Sudden topic growth
- Unusually inactive research periods

Uses Python standard library only.
"""

from __future__ import annotations

import math

from collections import Counter, defaultdict
from statistics import mean, pstdev
from typing import Any


def _safe_number(value: Any) -> float:
    """Convert a value into a non-negative number."""

    try:
        return max(0.0, float(value or 0))
    except (ValueError, TypeError):
        return 0.0


def _calculate_z_score(
    value: float,
    historical_values: list[float],
) -> float:
    """Calculate a z-score against historical observations."""

    if not historical_values:
        return 0.0

    average = mean(historical_values)

    deviation = pstdev(historical_values)

    if deviation == 0:

        if value > average:
            return 10.0

        if value < average:
            return -10.0

        return 0.0

    return (value - average) / deviation


def detect_anomalies(
    historical_values: list[float],
    current_value: float,
    threshold: float = 2.0,
    metric_name: str = "research_activity",
) -> dict[str, Any]:
    """
    Detect whether a current metric is statistically unusual.

    Args:
        historical_values:
            Previous observations in chronological order.

        current_value:
            Current observation.

        threshold:
            Absolute z-score required to flag an anomaly.

        metric_name:
            Name of the metric being analyzed.

    Returns:
        JSON-serializable anomaly result.
    """

    if threshold <= 0:
        raise ValueError(
            "threshold must be greater than zero."
        )

    historical = [
        _safe_number(value)
        for value in historical_values
    ]

    current = _safe_number(current_value)

    if len(historical) < 3:

        return {
            "success": True,
            "metric": metric_name,
            "is_anomaly": False,
            "anomaly_type": "insufficient_history",
            "current_value": current,
            "historical_average": (
                round(mean(historical), 3)
                if historical else None
            ),
            "z_score": None,
            "threshold": threshold,
            "message": (
                "At least three historical observations "
                "are required."
            ),
        }

    average = mean(historical)

    z_score = _calculate_z_score(
        current,
        historical,
    )

    is_anomaly = abs(z_score) >= threshold

    if z_score >= threshold:
        anomaly_type = "spike"

    elif z_score <= -threshold:
        anomaly_type = "drop"

    else:
        anomaly_type = "normal"

    return {
        "success": True,
        "metric": metric_name,
        "is_anomaly": is_anomaly,
        "anomaly_type": anomaly_type,
        "current_value": round(current, 3),
        "historical_average": round(average, 3),
        "z_score": round(z_score, 3),
        "threshold": threshold,
        "message": (
            f"Unusual {anomaly_type} detected in {metric_name}."
            if is_anomaly
            else f"{metric_name} is within the expected range."
        ),
    }


def analyze_publication_volume(
    papers: list[dict[str, Any]],
    period_field: str = "publication_year",
    threshold: float = 2.0,
) -> dict[str, Any]:
    """
    Analyze annual publication volume and detect anomalies.

    Example paper:
        {
            "paper_id": "paper-001",
            "publication_year": 2025
        }
    """

    yearly_counts = Counter()

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        period = paper.get(period_field)

        try:
            period = int(period)
        except (ValueError, TypeError):
            continue

        yearly_counts[period] += 1

    if not yearly_counts:

        return {
            "success": True,
            "metric": "publication_volume",
            "period_field": period_field,
            "periods_analyzed": 0,
            "anomalies": [],
            "message": "No valid publication dates found.",
        }

    periods = sorted(yearly_counts)

    observations = []

    anomalies = []

    for index, period in enumerate(periods):

        current_value = yearly_counts[period]

        history = observations[-5:]

        result = detect_anomalies(
            historical_values=history,
            current_value=current_value,
            threshold=threshold,
            metric_name="publication_volume",
        )

        if result["is_anomaly"]:

            anomalies.append({
                "period": period,
                "value": current_value,
                "anomaly_type": result["anomaly_type"],
                "z_score": result["z_score"],
                "historical_average": result[
                    "historical_average"
                ],
            })

        observations.append(
            float(current_value)
        )

    return {
        "success": True,
        "metric": "publication_volume",
        "period_field": period_field,
        "periods_analyzed": len(periods),
        "yearly_data": [
            {
                "period": period,
                "publication_count": yearly_counts[period],
            }
            for period in periods
        ],
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }


def analyze_citation_activity(
    papers: list[dict[str, Any]],
    period_field: str = "publication_year",
    threshold: float = 2.0,
) -> dict[str, Any]:
    """
    Analyze total citations per publication year.

    Note:
    Citation counts are cumulative values from the source.
    This function detects unusual yearly totals, not
    actual time-series citation growth.
    """

    yearly_citations = defaultdict(float)

    for paper in papers:

        if not isinstance(paper, dict):
            continue

        period = paper.get(period_field)

        try:
            period = int(period)
        except (ValueError, TypeError):
            continue

        citations = _safe_number(
            paper.get("citation_count")
        )

        yearly_citations[period] += citations

    periods = sorted(yearly_citations)

    history = []
    anomalies = []

    for period in periods:

        current = yearly_citations[period]

        result = detect_anomalies(
            historical_values=history[-5:],
            current_value=current,
            threshold=threshold,
            metric_name="citation_activity",
        )

        if result["is_anomaly"]:

            anomalies.append({
                "period": period,
                "citation_count": round(current, 2),
                "anomaly_type": result["anomaly_type"],
                "z_score": result["z_score"],
            })

        history.append(current)

    return {
        "success": True,
        "metric": "citation_activity",
        "periods_analyzed": len(periods),
        "yearly_data": [
            {
                "period": period,
                "citation_count": round(
                    yearly_citations[period],
                    2,
                ),
            }
            for period in periods
        ],
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
    }


def detect_emerging_topics(
    historical_topic_counts: dict[str, int],
    current_topic_counts: dict[str, int],
    minimum_growth: float = 0.5,
    minimum_count: int = 3,
) -> dict[str, Any]:
    """
    Detect topics growing compared with a previous period.

    Growth rate:
        (current - previous) / previous

    New topics are reported separately.
    """

    if not 0 <= minimum_growth:
        raise ValueError(
            "minimum_growth cannot be negative."
        )

    if minimum_count < 1:
        raise ValueError(
            "minimum_count must be at least 1."
        )

    previous = {
        str(topic).strip().lower(): int(count)
        for topic, count in historical_topic_counts.items()
        if topic and int(count) >= 0
    }

    current = {
        str(topic).strip().lower(): int(count)
        for topic, count in current_topic_counts.items()
        if topic and int(count) >= 0
    }

    emerging = []

    for topic, current_count in current.items():

        previous_count = previous.get(topic, 0)

        if current_count < minimum_count:
            continue

        if previous_count == 0:

            growth_rate = None
            topic_type = "new_topic"

            emerging.append({
                "topic": topic,
                "previous_count": 0,
                "current_count": current_count,
                "growth_rate": growth_rate,
                "topic_type": topic_type,
            })

            continue

        growth_rate = (
            current_count - previous_count
        ) / previous_count

        if growth_rate >= minimum_growth:

            emerging.append({
                "topic": topic,
                "previous_count": previous_count,
                "current_count": current_count,
                "growth_rate": round(
                    growth_rate,
                    4,
                ),
                "topic_type": "growing_topic",
            })

    emerging.sort(
        key=lambda item: (
            item["current_count"],
            item["growth_rate"] or 0,
        ),
        reverse=True,
    )

    return {
        "success": True,
        "metric": "emerging_topics",
        "total": len(emerging),
        "results": emerging,
    }
