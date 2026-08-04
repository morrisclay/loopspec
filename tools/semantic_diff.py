"""Deterministic semantic comparison for validated LoopSpec documents."""

from collections import Counter
import hashlib
import json


def normalize_value(value):
    """Canonicalize unordered IR values without depending on Python hash or YAML order."""
    if isinstance(value, dict):
        return {key: normalize_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        items = [normalize_value(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True,
                                                         separators=(",", ":")))
    return value


def normalize_brand_for_hash(value):
    """Keep the URAS→LoopSpec rename from masquerading as a diagnostic meaning change."""
    if isinstance(value, dict):
        return {key: normalize_brand_for_hash(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_brand_for_hash(item) for item in value]
    if isinstance(value, str):
        return value.replace("LoopSpec", "URAS").replace("loopspec", "uras")
    return value


def semantic_hash(document):
    """Hash canonical meaning, independent of serialization and collection order."""
    canonical = dict(document)
    if "loopspec_version" in canonical and "uras_version" not in canonical:
        # The 2026 project rename is metadata, not a semantic change. Preserve the v2.1
        # conformance hashes by using the historical wire spelling in the hash payload.
        canonical["uras_version"] = canonical.pop("loopspec_version")
    payload = json.dumps(normalize_value(canonical), sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def findings_hash(findings):
    """Hash the complete unordered finding set, including evidence and claim metadata."""
    payload = json.dumps(normalize_value(normalize_brand_for_hash(findings)), sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _field_changes(before, after, ignored=("id",)):
    changes = []
    keys = sorted((set(before) | set(after)) - set(ignored))
    for field in keys:
        left = normalize_value(before.get(field)) if field in before else None
        right = normalize_value(after.get(field)) if field in after else None
        if left != right:
            changes.append({"field": field, "before": left, "after": right})
    return changes


def _indexed_diff(before, after):
    left = {item["id"]: item for item in before}
    right = {item["id"]: item for item in after}
    added = [normalize_value(right[item_id]) for item_id in sorted(set(right) - set(left))]
    removed = [normalize_value(left[item_id]) for item_id in sorted(set(left) - set(right))]
    modified = []
    for item_id in sorted(set(left) & set(right)):
        changes = _field_changes(left[item_id], right[item_id])
        if changes:
            modified.append({"id": item_id, "changes": changes})
    return {"added": added, "removed": removed, "modified": modified}


def _edge_key(edge):
    return edge.get("from"), edge.get("rel"), edge.get("to")


def _edge_diff(before, after):
    left = {_edge_key(edge) for edge in before}
    right = {_edge_key(edge) for edge in after}

    def record(key):
        return {"from": key[0], "rel": key[1], "to": key[2]}

    return {
        "added": [record(key) for key in sorted(right - left)],
        "removed": [record(key) for key in sorted(left - right)],
    }


def _finding_key(finding):
    identity = {
        "pattern": finding.get("pattern"),
        "assurance": finding.get("assurance"),
        "evidence": normalize_value(finding.get("evidence") or {}),
    }
    return json.dumps(identity, sort_keys=True, separators=(",", ":"))


def _finding_diff(before, after):
    left_records = {}
    right_records = {}
    left = Counter()
    right = Counter()
    for finding in before:
        key = _finding_key(finding)
        left[key] += 1
        left_records[key] = normalize_value(finding)
    for finding in after:
        key = _finding_key(finding)
        right[key] += 1
        right_records[key] = normalize_value(finding)

    added = []
    removed = []
    for key in sorted(right - left):
        added.extend([right_records[key]] * (right[key] - left[key]))
    for key in sorted(left - right):
        removed.extend([left_records[key]] * (left[key] - right[key]))
    return {"added": added, "removed": removed}


def compare(left_document, right_document, left_findings=None, right_findings=None,
            left_spec=None, right_spec=None):
    """Return a stable, machine-readable semantic delta between two valid documents."""
    document_ignored = {
        "nodes", "edges", "loops", "loopspec_version", "uras_version", "ir_revision",
        "shape", "source_format"
    }
    left_header = {key: value for key, value in left_document.items()
                   if key not in document_ignored}
    right_header = {key: value for key, value in right_document.items()
                    if key not in document_ignored}
    delta = {
        "left": {
            "spec": left_spec,
            "encodes": left_document.get("encodes"),
            "ir_revision": left_document.get("ir_revision"),
            "semantic_hash": semantic_hash(left_document),
        },
        "right": {
            "spec": right_spec,
            "encodes": right_document.get("encodes"),
            "ir_revision": right_document.get("ir_revision"),
            "semantic_hash": semantic_hash(right_document),
        },
        "document": {"changes": _field_changes(left_header, right_header, ignored=())},
        "nodes": _indexed_diff(left_document.get("nodes") or [],
                               right_document.get("nodes") or []),
        "edges": _edge_diff(left_document.get("edges") or [],
                            right_document.get("edges") or []),
        "loops": _indexed_diff(left_document.get("loops") or [],
                               right_document.get("loops") or []),
        "findings": _finding_diff(left_findings or [], right_findings or []),
    }
    counts = {
        "document_fields_changed": len(delta["document"]["changes"]),
        "nodes_added": len(delta["nodes"]["added"]),
        "nodes_removed": len(delta["nodes"]["removed"]),
        "nodes_modified": len(delta["nodes"]["modified"]),
        "edges_added": len(delta["edges"]["added"]),
        "edges_removed": len(delta["edges"]["removed"]),
        "loops_added": len(delta["loops"]["added"]),
        "loops_removed": len(delta["loops"]["removed"]),
        "loops_modified": len(delta["loops"]["modified"]),
        "findings_added": len(delta["findings"]["added"]),
        "findings_removed": len(delta["findings"]["removed"]),
    }
    delta["summary"] = counts
    delta["changed"] = any(counts.values())
    return delta


def _short(value):
    rendered = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return rendered if len(rendered) <= 120 else rendered[:117] + "..."


def render(delta):
    """Render a concise human review of a semantic delta."""
    left = delta["left"]
    right = delta["right"]
    lines = [f"{left.get('encodes')} → {right.get('encodes')}"]
    if not delta["changed"]:
        return "\n".join(lines + ["No semantic changes."])

    summary = delta["summary"]
    lines.append(
        f"{sum(summary.values())} change record(s): "
        f"nodes +{summary['nodes_added']}/-{summary['nodes_removed']}/"
        f"~{summary['nodes_modified']}, "
        f"edges +{summary['edges_added']}/-{summary['edges_removed']}, "
        f"findings +{summary['findings_added']}/-{summary['findings_removed']}"
    )

    for change in delta["document"]["changes"]:
        lines.append(f"  ~ document.{change['field']}: "
                     f"{_short(change['before'])} → {_short(change['after'])}")
    for record in delta["nodes"]["added"]:
        lines.append(f"  + node {record['id']} ({record.get('kind')})")
    for record in delta["nodes"]["removed"]:
        lines.append(f"  - node {record['id']} ({record.get('kind')})")
    for record in delta["nodes"]["modified"]:
        for change in record["changes"]:
            lines.append(f"  ~ node {record['id']}.{change['field']}: "
                         f"{_short(change['before'])} → {_short(change['after'])}")
    for edge in delta["edges"]["added"]:
        lines.append(f"  + edge {edge['from']} -{edge['rel']}→ {edge['to']}")
    for edge in delta["edges"]["removed"]:
        lines.append(f"  - edge {edge['from']} -{edge['rel']}→ {edge['to']}")
    for record in delta["loops"]["added"]:
        lines.append(f"  + loop {record['id']}")
    for record in delta["loops"]["removed"]:
        lines.append(f"  - loop {record['id']}")
    for record in delta["loops"]["modified"]:
        for change in record["changes"]:
            lines.append(f"  ~ loop {record['id']}.{change['field']}: "
                         f"{_short(change['before'])} → {_short(change['after'])}")
    for finding in delta["findings"]["added"]:
        lines.append(f"  + finding [{finding.get('pattern')}] "
                     f"{finding.get('assurance')}")
    for finding in delta["findings"]["removed"]:
        lines.append(f"  - finding [{finding.get('pattern')}] "
                     f"{finding.get('assurance')}")
    return "\n".join(lines)
