from __future__ import annotations

from collections import Counter
from typing import Any

from .models import ScanReport


def compare_reports(before: ScanReport, after: ScanReport) -> dict[str, Any]:
    before_categories = Counter(f.category for f in before.findings)
    after_categories = Counter(f.category for f in after.findings)
    categories = sorted(set(before_categories) | set(after_categories))
    deltas = {
        category: {
            "before": before_categories[category],
            "after": after_categories[category],
            "delta": after_categories[category] - before_categories[category],
        }
        for category in categories
    }
    before_ids = {f.id for f in before.findings}
    after_ids = {f.id for f in after.findings}
    before_by_category = {f.category: f for f in before.findings}
    after_by_category = {f.category: f for f in after.findings}
    severity_changed = sorted(
        category for category in before_by_category.keys() & after_by_category.keys()
        if before_by_category[category].severity != after_by_category[category].severity
    )
    evidence_changed = sorted(
        category for category in before_by_category.keys() & after_by_category.keys()
        if before_by_category[category].evidence != after_by_category[category].evidence
    )
    return {
        "before_session": before.session.id,
        "after_session": after.session.id,
        "before_total": len(before.findings),
        "after_total": len(after.findings),
        "net_change": len(after.findings) - len(before.findings),
        "category_deltas": deltas,
        "resolved_finding_ids": sorted(before_ids - after_ids),
        "new_finding_ids": sorted(after_ids - before_ids),
        "persistent_finding_ids": sorted(before_ids & after_ids),
        "severity_changed": severity_changed,
        "evidence_changed": evidence_changed,
        "relocated": sorted(set(evidence_changed) - set(severity_changed)),
        "policy_added": sorted(set(after_by_category) - set(before_by_category)),
        "policy_removed": sorted(set(before_by_category) - set(after_by_category)),
        "finding_status": {
            **{finding_id: "resolved" for finding_id in sorted(before_ids - after_ids)},
            **{finding_id: "new" for finding_id in sorted(after_ids - before_ids)},
            **{finding_id: "persistent" for finding_id in sorted(before_ids & after_ids)},
        },
    }
