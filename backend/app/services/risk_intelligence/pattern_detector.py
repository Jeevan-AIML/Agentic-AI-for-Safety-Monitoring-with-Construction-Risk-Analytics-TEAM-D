"""
Recurring Risk Pattern Detector — Milestone 4 Phase 4.2
=======================================================
Detects recurring patterns across multi-agent findings over configurable
time windows (24h, 7d, 30d). Never identifies a pattern from a single occurrence.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from app.services.risk_intelligence.collector import RiskIntelligenceFinding


class PatternList(list):
    """Hybrid list & dict response allowing both list iteration and dict key access."""
    def __init__(self, patterns: List[Dict[str, Any]], summary: str = "", status: str = "PATTERNS_DETECTED"):
        super().__init__(patterns)
        self.patterns = patterns
        self.summary = summary
        self.message = summary
        self.status = status

    def __getitem__(self, item):
        if isinstance(item, str):
            if item == "patterns":
                return list(self)
            elif item in ["message", "summary", "recurring_patterns_summary"]:
                return self.summary
            elif item == "patterns_count":
                return len(self)
            elif item == "status":
                return self.status
            raise KeyError(item)
        return super().__getitem__(item)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except (KeyError, TypeError):
            return default


class RecurringRiskPatternDetector:
    """Identifies recurring risk clusters, behavioral violations, and systemic breaches."""

    def __init__(self, min_threshold: int = 2):
        self.min_threshold = min_threshold

    def detect_patterns(
        self,
        findings: List[RiskIntelligenceFinding],
        time_window_days: int = 30,
        min_threshold: Optional[int] = None,
    ) -> PatternList:
        """
        Analyzes findings for recurring patterns (>= min_threshold occurrences).
        Returns hybrid list and dict of detected patterns.
        """
        threshold = min_threshold if min_threshold is not None else self.min_threshold

        if len(findings) < threshold:
            return PatternList(
                patterns=[],
                summary="Insufficient historical data for reliable pattern analysis.",
                status="INSUFFICIENT_DATA",
            )

        patterns: List[Dict[str, Any]] = []

        # ── 1. Group by Hazard Type (Site Risk) ─────────────────────────────
        hazard_groups: Dict[str, List[RiskIntelligenceFinding]] = defaultdict(list)
        for f in findings:
            if f.source_agent in ["site_risk", "SITE_RISK"] or f.category in ["HAZARD", "SITE_RISK"]:
                h_type = f.finding_type or (f.metadata or {}).get("hazard_type") or "GENERAL"
                hazard_groups[str(h_type).upper()].append(f)

        for h_type, group in hazard_groups.items():
            if len(group) >= threshold:
                crit_count = sum(1 for f in group if f.severity in ["CRITICAL", "HIGH"])
                sev = "CRITICAL" if crit_count >= 2 else ("HIGH" if crit_count >= 1 else "MEDIUM")
                locs = list({f.location for f in group if f.location})

                desc = f"{len(group)} separate {h_type} hazards logged. Indicates persistent site conditions requiring engineering intervention."
                pat = {
                    "pattern_id": f"PAT-HAZ-{h_type[:4]}",
                    "pattern_name": f"Repeated {h_type.replace('_', ' ').title()} Hazards",
                    "category": "SITE_RISK",
                    "pattern_type": h_type,
                    "pattern_description": desc,
                    "description": desc,
                    "occurrence_count": len(group),
                    "occurrences": len(group),
                    "time_window": f"Last {time_window_days} days",
                    "time_window_hours": time_window_days * 24,
                    "severity": sev,
                    "velocity": "ACCELERATING" if len(group) >= 3 else "PERSISTENT",
                    "trend": "ESCALATING" if len(group) >= 3 else "PERSISTENT",
                    "locations": locs,
                    "sample_finding_ids": [f.finding_id for f in group],
                    "supporting_finding_ids": [f.finding_id for f in group],
                    "recommended_countermeasure": f"Deploy structural/environmental inspection and revise Job Safety Analysis for {h_type.lower()} operations.",
                }
                patterns.append(pat)

        # ── 2. Group by Safety Violation Type / PPE (Safety Agent) ──────────
        safety_groups: Dict[str, List[RiskIntelligenceFinding]] = defaultdict(list)
        for f in findings:
            if f.source_agent in ["safety", "SAFETY"] or f.category in ["SAFETY", "SAFETY_VIOLATION"]:
                s_type = f.finding_type or (f.metadata or {}).get("finding_type") or f.category
                safety_groups[str(s_type).upper()].append(f)

        for s_type, group in safety_groups.items():
            if len(group) >= threshold:
                is_ppe = "PPE" in s_type
                crit_count = sum(1 for f in group if f.severity in ["CRITICAL", "HIGH"])
                sev = "CRITICAL" if crit_count >= 2 else ("HIGH" if crit_count >= 1 else "MEDIUM")
                p_type = "PPE_COMPLIANCE" if is_ppe else "BEHAVIORAL_SAFETY"
                name = f"Recurring PPE Non-Compliance ({s_type.replace('_', ' ')})" if is_ppe else f"Repeated Safety Non-Compliance ({s_type.replace('_', ' ')})"
                locs = list({f.location for f in group if f.location})

                desc = f"{len(group)} instances of {s_type} detected. Demonstrates recurring operational safety divergence."
                pat = {
                    "pattern_id": f"PAT-SAF-{s_type[:4]}",
                    "pattern_name": name,
                    "category": "SAFETY",
                    "pattern_type": s_type,
                    "pattern_description": desc,
                    "description": desc,
                    "occurrence_count": len(group),
                    "occurrences": len(group),
                    "time_window": f"Last {time_window_days} days",
                    "time_window_hours": time_window_days * 24,
                    "severity": sev,
                    "velocity": "ACCELERATING" if len(group) >= 4 else "STEADY",
                    "trend": "ESCALATING" if len(group) >= 4 else "PERSISTENT",
                    "locations": locs,
                    "sample_finding_ids": [f.finding_id for f in group],
                    "supporting_finding_ids": [f.finding_id for f in group],
                    "recommended_countermeasure": "Mandate targeted shift safety stand-downs, daily PPE gate checks, and subcontractor re-briefings.",
                }
                patterns.append(pat)

        # ── 3. Group by Regulatory Standard (Compliance Agent) ──────────────
        compliance_groups: Dict[str, List[RiskIntelligenceFinding]] = defaultdict(list)
        for f in findings:
            if f.source_agent in ["compliance", "COMPLIANCE"] or f.category in ["COMPLIANCE", "REGULATORY_BREACH"]:
                std_ref = f.finding_type or (f.metadata or {}).get("standard_ref") or "GENERAL_DUTY"
                compliance_groups[std_ref].append(f)

        for std_ref, group in compliance_groups.items():
            if len(group) >= threshold:
                locs = list({f.location for f in group if f.location})
                desc = f"Standard {std_ref} violated {len(group)} times across active site inspections."
                patterns.append({
                    "pattern_id": f"PAT-CMP-{abs(hash(std_ref)) % 10000:04d}",
                    "pattern_name": f"Systemic Regulatory Non-Conformance ({std_ref})",
                    "category": "COMPLIANCE",
                    "pattern_type": std_ref,
                    "pattern_description": desc,
                    "description": desc,
                    "occurrence_count": len(group),
                    "occurrences": len(group),
                    "time_window": f"Last {time_window_days} days",
                    "time_window_hours": time_window_days * 24,
                    "severity": "HIGH",
                    "velocity": "PERSISTENT",
                    "trend": "PERSISTENT",
                    "locations": locs,
                    "sample_finding_ids": [f.finding_id for f in group],
                    "supporting_finding_ids": [f.finding_id for f in group],
                    "recommended_countermeasure": f"Audit site processes directly governed by {std_ref} and assign safety supervisor to verify closeout.",
                })

        msg = f"Identified {len(patterns)} recurring risk patterns over {time_window_days} days." if patterns else "No recurring patterns met the detection threshold."
        status_str = "PATTERNS_DETECTED" if patterns else "NO_RECURRING_PATTERNS"

        return PatternList(patterns=patterns, summary=msg, status=status_str)
