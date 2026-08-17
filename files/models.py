"""
Core data model for the Product Trust Engine.
Matches Product-Trust-Engine-Appliances-CategoryConfig-v1.md Section 5.
Pure data classes, no I/O, no network — fully unit-testable in isolation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone


@dataclass
class Evidence:
    source_url: str
    source_tier: int  # 0-5, see category config Section 2
    page_or_section: str = ""
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    content_checksum: str = ""


@dataclass
class ValidationEntry:
    rule: str
    result: str  # "PASS" | "FAIL"
    severity: str = "info"  # info | low | medium | high
    reason: str = ""


@dataclass
class HistoryEntry:
    value: str
    timestamp: str
    evidence_ref: str
    reason: str


@dataclass
class Identity:
    status: str  # "verified" | "unverified"
    matched_on: str = "manufacturer_part_number"


@dataclass
class Attribute:
    attribute: str
    value: Optional[str] = None
    uom: Optional[str] = None
    status: str = "unknown"  # verified | needs_review | unknown
    confidence: float = 0.0
    evidence: list[Evidence] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)
    validation_report: list[ValidationEntry] = field(default_factory=list)
    history: list[HistoryEntry] = field(default_factory=list)
    required: bool = False

    def to_dict(self) -> dict:
        return {
            "attribute": self.attribute,
            "value": self.value,
            "uom": self.uom,
            "status": self.status,
            "confidence": round(self.confidence, 3),
            "evidence": [vars(e) for e in self.evidence],
            "checks": self.checks,
            "validation_report": [vars(v) for v in self.validation_report],
            "history": [vars(h) for h in self.history],
        }


@dataclass
class Product:
    mfg_part_num: str
    part_desc: str
    identity: Identity = field(default_factory=lambda: Identity(status="unverified"))
    manufacturer_name: Optional[str] = None
    brand_name: Optional[str] = None
    classpath: Optional[str] = None
    classpath_confidence: float = 0.0
    attributes: list[Attribute] = field(default_factory=list)
    quality_score: dict = field(default_factory=dict)
    descriptions: dict = field(default_factory=dict)

    def get_attr(self, name: str) -> Optional[Attribute]:
        for a in self.attributes:
            if a.attribute == name:
                return a
        return None

    def to_dict(self) -> dict:
        return {
            "mfg_part_num": self.mfg_part_num,
            "part_desc": self.part_desc,
            "identity": vars(self.identity),
            "manufacturer_name": self.manufacturer_name,
            "brand_name": self.brand_name,
            "classpath": self.classpath,
            "classpath_confidence": round(self.classpath_confidence, 3),
            "attributes": [a.to_dict() for a in self.attributes],
            "quality_score": self.quality_score,
            "descriptions": self.descriptions,
        }
