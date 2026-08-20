"""
Evidence retrieval is abstracted behind EvidenceProvider so the pipeline
itself never depends on a specific search/fetch backend.

Evidence providers return real, sourced data — no hardcoded values.
Each fact includes a source URL, tier (0-5), and retrieval timestamp.

Providers:
- WebEvidenceProvider: live manufacturer page scraping
- PDFEvidenceProvider: spec sheet PDF extraction
- DescriptionExtractionProvider: Doc-First extraction from Part_Desc
- AgenticEvidenceProvider: LLM-based web research (optional)
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from models import Evidence


class EvidenceProvider(ABC):
    @abstractmethod
    def fetch(self, mfg_part_num: str) -> dict:
        """Return a dict of {field_name: (value, uom, Evidence)} for a given MPN."""
        raise NotImplementedError
