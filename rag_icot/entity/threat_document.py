from dataclasses import dataclass
from typing import Optional


@dataclass
class ThreatDocument:

    source: str
    document_type: str

    title: Optional[str] = None
    description: Optional[str] = None

    cve: Optional[str] = None

    attack_type: Optional[str] = None

    protocol: Optional[str] = None

    source_ip: Optional[str] = None

    destination_ip: Optional[str] = None

    severity: Optional[str] = None

    metadata: Optional[dict] = None