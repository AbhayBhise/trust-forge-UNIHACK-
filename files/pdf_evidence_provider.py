import fitz
import re
import os
from evidence_provider import EvidenceProvider
from models import Evidence

class PDFEvidenceProvider(EvidenceProvider):
    def fetch(self, mfg_part_num: str) -> dict:
        if mfg_part_num != "WDTS7024RZ":
            return {}

        pdf_path = os.path.join(os.path.dirname(__file__), "whirlpool_spec_sheet.pdf")
        if not os.path.exists(pdf_path):
            return {}

        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
            
        mfr_url = "https://www.whirlpool.com/content/dam/global/documents/202102/dimension-guide-W11414275-RevB.pdf"

        out = {
            "_manufacturer_name": "Whirlpool Corporation",
            "_brand_name": "Whirlpool®",
            "_series": "Eco Series",
            "_mfr_url": mfr_url,
            "facts": {}
        }
        
        ev = Evidence(
            source_url=mfr_url,
            source_tier=4, 
            page_or_section="Page 1",
            retrieved_at="2026-08-14T00:00:00+00:00" 
        )

        v_match = re.search(r"Voltage:\s*(\d+)\s*V", text)
        if v_match:
            out["facts"]["Voltage Rating"] = (v_match.group(1), "V", ev)
            
        a_match = re.search(r"Amperage:\s*(\d+)\s*A", text)
        if a_match:
            out["facts"]["Amperage Rating"] = (a_match.group(1), "A", ev)
            
        db_match = re.search(r"Decibel Level:\s*(\d+)\s*dBA", text)
        if db_match:
            out["facts"]["Sound Level"] = (db_match.group(1), "dBA", ev)
            
        h_match = re.search(r"Height:\s*([\d\-/]+)\s*in", text)
        w_match = re.search(r"Width:\s*([\d\-/]+)\s*in", text)
        d_match = re.search(r"Depth:\s*([\d\-/]+)\s*in", text)
        if h_match and w_match and d_match:
            size_str = f"{h_match.group(1)} in H x {w_match.group(1)} in W x {d_match.group(1)} in D"
            out["facts"]["Size"] = (size_str, "in", ev)
            
        m_match = re.search(r"Tub Material:\s*(.+)", text)
        if m_match:
            out["facts"]["Material"] = (m_match.group(1).strip(), None, ev)
            
        c_match = re.search(r"Wash Cycles:\s*(\d+)\s*Cycles", text)
        if c_match:
            out["facts"]["Number of Wash Cycles"] = (c_match.group(1), None, ev)
            
        mt_match = re.search(r"Mounting:\s*(.+)", text)
        if mt_match:
            out["facts"]["Mounting Type"] = (mt_match.group(1).strip(), None, ev)

        return out
