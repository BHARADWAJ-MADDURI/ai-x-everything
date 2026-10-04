import re

from src.rendering.carousel.models import DiagramSpec, EditorialGraphicSpec


ALLOWED_DIAGRAM_LABELS = {
    "requires",
    "reduces",
    "supports",
    "uses",
    "leads to",
    "validated by",
    "depends on",
}
NUMERIC_RE = re.compile(r"[$]\d|\d[\d,]*(?:\.\d+)?(?:%|x)?")


def validate_diagram_spec(spec: DiagramSpec, verified_claim_ids: set[str]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not spec.supporting_claim_ids:
        issues.append("diagram requires supporting claim references")
    _require_known_claims(spec.supporting_claim_ids, verified_claim_ids, issues)
    node_ids = {node.node_id for node in spec.nodes}
    for node in spec.nodes:
        _require_known_claims(node.supporting_claim_ids, verified_claim_ids, issues)
    for edge in spec.edges:
        if edge.from_node not in node_ids or edge.to_node not in node_ids:
            issues.append("diagram edge references an unknown node")
        if edge.label.lower() not in ALLOWED_DIAGRAM_LABELS:
            issues.append("unsupported diagram relationship")
        _require_known_claims(edge.supporting_claim_ids, verified_claim_ids, issues)
    return not issues, issues


def validate_editorial_graphic(spec: EditorialGraphicSpec, verified_claim_text: str) -> tuple[bool, list[str]]:
    issues: list[str] = []
    if not spec.supporting_claim_ids:
        issues.append("editorial graphic requires supporting claim references")
    if spec.value and NUMERIC_RE.search(spec.value) and spec.value not in verified_claim_text:
        issues.append("unsupported numeric visual")
    return not issues, issues


def _require_known_claims(claim_ids: list[str], verified_claim_ids: set[str], issues: list[str]) -> None:
    for claim_id in claim_ids:
        if claim_id not in verified_claim_ids:
            issues.append(f"invalid claim reference {claim_id}")
