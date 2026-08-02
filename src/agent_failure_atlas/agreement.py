"""Inter-reviewer agreement and unanimous-consensus utilities."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from .annotations import AnnotationLabel, TraceAnnotation

ReviewKey = tuple[str, str, str]
ELIGIBLE_LABELS = {AnnotationLabel.POSITIVE, AnnotationLabel.NEGATIVE}


@dataclass(frozen=True)
class ConsensusLabel:
    session_id: str
    failure_category: str
    review_round: str
    label: AnnotationLabel
    source_type: str
    reviewer_ids: tuple[str, ...]


def _reviewed_groups(
    annotations: Iterable[TraceAnnotation],
) -> tuple[dict[ReviewKey, dict[str, TraceAnnotation]], int]:
    groups: dict[ReviewKey, dict[str, TraceAnnotation]] = defaultdict(dict)
    excluded = 0
    for annotation in annotations:
        if annotation.label not in ELIGIBLE_LABELS or not annotation.failure_category:
            excluded += 1
            continue
        key = (
            annotation.session_id,
            annotation.failure_category,
            annotation.review_round,
        )
        if annotation.reviewer_id in groups[key]:
            raise ValueError(
                "Duplicate reviewer annotation for "
                f"{annotation.session_id}/{annotation.failure_category}"
            )
        groups[key][annotation.reviewer_id] = annotation
    return dict(groups), excluded


def agreement_summary(annotations: Iterable[TraceAnnotation]) -> dict:
    groups, excluded = _reviewed_groups(annotations)
    reviewed_items = []
    total_positive = 0
    total_negative = 0
    item_agreements = []
    conflicts = []

    for key, by_reviewer in sorted(groups.items()):
        if len(by_reviewer) < 2:
            continue
        labels = [annotation.label for annotation in by_reviewer.values()]
        positive = labels.count(AnnotationLabel.POSITIVE)
        negative = labels.count(AnnotationLabel.NEGATIVE)
        total = len(labels)
        observed = ((positive * positive + negative * negative) - total) / (
            total * (total - 1)
        )
        item_agreements.append(observed)
        total_positive += positive
        total_negative += negative
        item = {
            "session_id": key[0],
            "failure_category": key[1],
            "review_round": key[2],
            "reviewers": sorted(by_reviewer),
            "positive": positive,
            "negative": negative,
            "agreement": round(observed, 4),
        }
        reviewed_items.append(item)
        if positive and negative:
            conflicts.append(item)

    rating_count = total_positive + total_negative
    if not reviewed_items or not rating_count:
        return {
            "reviewed_items": 0,
            "eligible_ratings": 0,
            "excluded_ratings": excluded,
            "observed_agreement": None,
            "expected_agreement": None,
            "fleiss_kappa": None,
            "conflicts": [],
            "items": [],
        }

    observed_agreement = sum(item_agreements) / len(item_agreements)
    positive_rate = total_positive / rating_count
    negative_rate = total_negative / rating_count
    expected_agreement = positive_rate * positive_rate + negative_rate * negative_rate
    kappa = (
        (observed_agreement - expected_agreement) / (1 - expected_agreement)
        if expected_agreement < 1
        else 1.0
    )
    return {
        "reviewed_items": len(reviewed_items),
        "eligible_ratings": rating_count,
        "excluded_ratings": excluded,
        "observed_agreement": round(observed_agreement, 4),
        "expected_agreement": round(expected_agreement, 4),
        "fleiss_kappa": round(kappa, 4),
        "conflicts": conflicts,
        "items": reviewed_items,
    }


def consensus_annotations(
    annotations: Iterable[TraceAnnotation], *, minimum_reviewers: int = 2
) -> tuple[list[ConsensusLabel], dict]:
    if minimum_reviewers < 2:
        raise ValueError("minimum_reviewers must be at least 2")
    annotation_list = list(annotations)
    groups, _ = _reviewed_groups(annotation_list)
    consensus: list[ConsensusLabel] = []

    for key, by_reviewer in sorted(groups.items()):
        if len(by_reviewer) < minimum_reviewers:
            continue
        labels = {annotation.label for annotation in by_reviewer.values()}
        source_types = {annotation.source_type for annotation in by_reviewer.values()}
        if len(labels) != 1 or len(source_types) != 1:
            continue
        consensus.append(
            ConsensusLabel(
                session_id=key[0],
                failure_category=key[1],
                review_round=key[2],
                label=next(iter(labels)),
                source_type=next(iter(source_types)),
                reviewer_ids=tuple(sorted(by_reviewer)),
            )
        )
    return consensus, agreement_summary(annotation_list)
