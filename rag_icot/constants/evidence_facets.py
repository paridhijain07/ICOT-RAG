"""Evidence facets used for sufficiency checks in ICOT-RAG."""

# Facets an IoT cybersecurity answer may need
EVIDENCE_FACETS = (
    "behaviour",       # IoT-23 traffic / malware behaviour
    "technique",       # MITRE ATT&CK technique / tactic
    "vulnerability",   # CVE / VARIoT vulnerability
    "exploit",         # exploit / PoC evidence
    "mitigation",      # defensive guidance (usually MITRE/detection)
)

# Map facet -> Chroma metadata filter
FACET_FILTERS = {
    "behaviour": {"source": "IoT23"},
    "technique": {"source": "MITRE"},
    "vulnerability": {
        "source": "VARIoT",
        "document_type": "vulnerability",
    },
    "exploit": {
        "source": "VARIoT",
        "document_type": "exploit",
    },
    "mitigation": {"source": "MITRE"},
}

VALID_SOURCES = ("MITRE", "VARIoT", "IoT23")
