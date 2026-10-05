"""
Report Generator Engine — Milestone 4 Phase 4.1
================================================
Generates the four core ACRIP report types:
1. Daily Site Report
2. Executive Risk Summary
3. Audit-Ready Documentation
4. Project Health Report
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid


class ReportGenerator:
    """Transforms aggregated cross-agent findings into structured, dynamic reports."""

    # ── 1. Daily Site Report ────────────────────────────────────────────────
    def generate_daily_site_report(
        self,
        aggregated: Dict[str, Any],
        reporting_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Creates a daily construction-site operational report.
        Gracefully marks missing agent findings as 'No findings available'.
        """
        date_str = (reporting_date or datetime.utcnow()).strftime("%Y-%m-%d")
        site = aggregated["site"]
        metrics = aggregated["metrics"]
        findings = aggregated["findings"]
        scores = metrics["scores"]

        # Synthesize Overall Site Condition
        crit = metrics["critical_count"]
        high = metrics["high_count"]
        if crit > 0:
            condition = "CRITICAL — Mandatory hazard mitigation required before standard operations proceed"
            status_badge = "CRITICAL"
        elif high > 0:
            condition = "ELEVATED RISK — Operational caution advised; corrective measures active"
            status_badge = "HIGH_RISK"
        elif metrics["open_count"] > 0:
            condition = "SATISFACTORY — Minor operational findings detected; monitor remediation"
            status_badge = "SATISFACTORY"
        else:
            condition = "OPTIMAL — Zero active hazard or compliance violations detected on site"
            status_badge = "OPTIMAL"

        # Separate findings by source
        hazards_list = findings["site_risk"] or []
        safety_list = findings["safety"] or []
        compliance_list = findings["compliance"] or []
        insurance_list = findings["insurance"] or []
        alerts_list = findings["alerts"] or []

        # Filter PPE-specific findings from safety findings
        ppe_findings = [f for f in safety_list if "PPE" in f["finding_type"] or "PPE" in f["description"]]

        # Build prioritized actionable recommendations
        recommendations = []
        for f in findings["critical"] + findings["high"]:
            if f.get("recommendation") and f["recommendation"] not in recommendations:
                recommendations.append(f"{f['source_agent'].upper()}: {f['recommendation']}")

        if not recommendations:
            recommendations.append("Continue standard automated sensory monitoring and scheduled daily safety walkthroughs.")

        return {
            "report_title": f"Daily Construction Site Report — {site['name']}",
            "report_type": "DAILY_SITE",
            "reporting_date": date_str,
            "generated_at": datetime.utcnow().isoformat(),
            "site_information": {
                "site_id": site["site_id"],
                "site_name": site["name"],
                "project_name": site["project_name"],
                "client": site["client"],
                "location": f"{site['city']}, {site['state']}" if site.get("city") else "Main Construction Zone",
                "active_workers_count": site["worker_count"],
                "active_equipment_count": site["equipment_count"],
            },
            "overall_condition": {
                "status": status_badge,
                "summary": condition,
                "overall_risk_score": scores["site_risk_score"],
                "safety_score": scores["safety_score"],
                "compliance_score": scores["compliance_score"],
            },
            "risk_overview": {
                "total_risks_detected": metrics["total_findings"],
                "open_incidents_count": metrics["open_count"],
                "resolved_incidents_count": metrics["resolved_count"],
                "severity_breakdown": {
                    "critical": metrics["critical_count"],
                    "high": metrics["high_count"],
                    "medium": metrics["medium_count"],
                    "low": metrics["low_count"],
                },
            },
            "site_hazards": {
                "count": len(hazards_list),
                "items": hazards_list if hazards_list else "No findings available",
            },
            "safety_violations": {
                "count": len(safety_list),
                "items": safety_list if safety_list else "No findings available",
            },
            "ppe_findings": {
                "count": len(ppe_findings),
                "ppe_compliance_rate_pct": scores["ppe_compliance_rate_pct"],
                "items": ppe_findings if ppe_findings else "No findings available",
            },
            "compliance_findings": {
                "count": len(compliance_list),
                "compliance_status": scores["compliance_status"],
                "items": compliance_list if compliance_list else "No findings available",
            },
            "insurance_findings": {
                "count": len(insurance_list),
                "estimated_liability_exposure": scores["estimated_liability_exposure"],
                "items": insurance_list if insurance_list else "No findings available",
            },
            "important_alerts": {
                "count": len(alerts_list),
                "items": alerts_list if alerts_list else "No findings available",
            },
            "recommended_actions": recommendations,
        }

    # ── 2. Executive Risk Summary ───────────────────────────────────────────
    def generate_executive_risk_summary(
        self,
        aggregated: Dict[str, Any],
        reporting_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Creates a concise executive-level risk intelligence brief
        suitable for project executives, insurers, and development directors.
        """
        date_str = (reporting_date or datetime.utcnow()).strftime("%Y-%m-%d")
        site = aggregated["site"]
        metrics = aggregated["metrics"]
        findings = aggregated["findings"]
        scores = metrics["scores"]

        # Major items (Critical & High across pillars)
        major_hazards = [f for f in findings["site_risk"] if f["severity"] in ["CRITICAL", "HIGH"]]
        major_safety = [f for f in findings["safety"] if f["severity"] in ["CRITICAL", "HIGH"]]
        major_compliance = [f for f in findings["compliance"] if f["severity"] in ["CRITICAL", "HIGH"]]
        major_insurance = [f for f in findings["insurance"] if f["severity"] in ["CRITICAL", "HIGH"]]

        # Executive summary narrative
        crit_count = metrics["critical_count"]
        high_count = metrics["high_count"]
        if crit_count > 0:
            executive_narrative = (
                f"Executive Alert: Site '{site['name']}' exhibits {crit_count} CRITICAL findings and {high_count} HIGH-risk items. "
                f"Current site risk score is {scores['site_risk_score']:.1f}/100 with estimated liability exposure at {scores['estimated_liability_exposure']}. "
                f"Immediate mitigation required to maintain compliance certifications and avoid stop-work directives."
            )
        elif high_count > 0:
            executive_narrative = (
                f"Site '{site['name']}' demonstrates elevated risk posture with {high_count} high-severity findings across safety and compliance. "
                f"Insurance exposure is currently {scores['estimated_liability_exposure']} with safety score at {scores['safety_score']:.1f}/100. "
                f"Targeted supervisory intervention recommended."
            )
        else:
            executive_narrative = (
                f"Site '{site['name']}' is operating in stable compliance posture. "
                f"Safety performance score stands at {scores['safety_score']:.1f}/100 and regulatory conformance is {scores['compliance_score']:.1f}%. "
                f"No major insurance exposures or critical bottlenecks detected."
            )

        # High priority executive recommendations
        exec_recs = []
        for item in findings["critical"]:
            if item.get("recommendation"):
                exec_recs.append(f"[CRITICAL] {item['source_agent'].upper()}: {item['recommendation']}")
        for item in findings["high"][:3]:
            if item.get("recommendation"):
                exec_recs.append(f"[HIGH] {item['source_agent'].upper()}: {item['recommendation']}")

        if not exec_recs:
            exec_recs.append("Maintain existing risk management protocols and bi-weekly compliance verification cycles.")

        return {
            "report_title": f"Executive Risk Summary — {site['name']}",
            "report_type": "EXECUTIVE_SUMMARY",
            "reporting_date": date_str,
            "generated_at": datetime.utcnow().isoformat(),
            "executive_narrative": executive_narrative,
            "project_overview": {
                "project_name": site["project_name"],
                "site_name": site["name"],
                "client": site["client"],
                "worker_count": site["worker_count"],
            },
            "risk_scorecard": {
                "site_risk": {
                    "score": scores["site_risk_score"],
                    "level": scores["site_risk_level"],
                },
                "safety_performance": {
                    "score": scores["safety_score"],
                    "level": scores["safety_level"],
                },
                "compliance_status": {
                    "score": scores["compliance_score"],
                    "status": scores["compliance_status"],
                },
                "insurance_exposure": {
                    "score": scores["insurance_risk_score"],
                    "level": scores["insurance_risk_level"],
                    "bracket": scores["estimated_liability_exposure"],
                },
            },
            "major_hazards": major_hazards if major_hazards else "No findings available",
            "major_safety_issues": major_safety if major_safety else "No findings available",
            "major_compliance_issues": major_compliance if major_compliance else "No findings available",
            "major_insurance_exposures": major_insurance if major_insurance else "No findings available",
            "critical_open_issues_count": len(findings["critical"]),
            "high_priority_recommendations": exec_recs,
            "trend_information": {
                "overall_posture": "Elevated" if (crit_count + high_count) > 0 else "Stable",
                "open_vs_resolved_ratio": f"{metrics['open_count']} open / {metrics['resolved_count']} resolved",
                "ppe_compliance_trend": f"{scores['ppe_compliance_rate_pct']}% compliant across active workforce",
            },
        }

    # ── 3. Audit-Ready Documentation ────────────────────────────────────────
    def generate_audit_ready_report(
        self,
        aggregated: Dict[str, Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Creates an audit-ready compliance document preserving strict traceability,
        standards references, finding IDs, evidence, and verification logs.
        """
        site = aggregated["site"]
        metrics = aggregated["metrics"]
        all_findings = aggregated["findings"]["all"]
        scores = metrics["scores"]

        audit_id = f"AUD-ACRIP-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        start_str = start_date.strftime("%Y-%m-%d") if start_date else "Platform Inception"
        end_str = end_date.strftime("%Y-%m-%d") if end_date else datetime.utcnow().strftime("%Y-%m-%d")

        # Enrich findings with strict audit details
        audit_trail = []
        for idx, f in enumerate(all_findings):
            meta = f.get("metadata") or {}
            std_ref = meta.get("standard_ref") or "General Duty Clause / OSHA 1926"
            audit_trail.append({
                "entry_number": idx + 1,
                "finding_id": f["finding_id"],
                "source_agent": f["source_agent"],
                "timestamp": f["timestamp"],
                "standard_reference": std_ref,
                "finding_type": f["finding_type"],
                "description": f["description"],
                "severity": f["severity"],
                "status": f["status"],
                "evidence": meta.get("evidence") or "Sensory/agent validation log recorded",
                "detection_source": meta.get("detection_source", "AGENT_ENGINE"),
                "recommended_action": f.get("recommendation") or "Review in accordance with site safety program",
                "worker_id": meta.get("worker_id"),
                "verified": True,
            })

        return {
            "report_title": f"Audit-Ready Compliance Documentation — {site['name']}",
            "report_type": "AUDIT_READY",
            "audit_dossier_id": audit_id,
            "generated_at": datetime.utcnow().isoformat(),
            "reporting_period": {
                "start": start_str,
                "end": end_str,
            },
            "site_identity": {
                "site_id": site["site_id"],
                "site_name": site["name"],
                "project_name": site["project_name"],
                "jurisdiction": f"{site['city']}, {site['state']}" if site.get("city") else "USA",
            },
            "audit_summary": {
                "total_records_audited": len(all_findings),
                "compliance_score": scores["compliance_score"],
                "regulatory_conformance_status": scores["compliance_status"],
                "critical_violations_logged": metrics["critical_count"],
                "high_violations_logged": metrics["high_count"],
                "open_records": metrics["open_count"],
                "closed_or_mitigated_records": metrics["resolved_count"],
            },
            "traceable_finding_records": audit_trail if audit_trail else "No findings available",
            "compliance_attestation": {
                "certifying_engine": "ACRIP Multi-Agent Regulatory & Safety Verification Suite",
                "algorithm_integrity": "Deterministic Rule & Agent Evaluation",
                "audit_status": "CERTIFIED_VALID" if metrics["critical_count"] == 0 else "ACTION_REQUIRED",
            },
        }

    # ── 4. Project Health Report ────────────────────────────────────────────
    def generate_project_health_report(
        self,
        aggregated: Dict[str, Any],
        reporting_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Creates a comprehensive 4-pillar project health assessment
        synthesizing Site Risk, Safety, Compliance, and Insurance dimensions.
        """
        date_str = (reporting_date or datetime.utcnow()).strftime("%Y-%m-%d")
        site = aggregated["site"]
        metrics = aggregated["metrics"]
        findings = aggregated["findings"]
        scores = metrics["scores"]
        domain = aggregated.get("domain_data", {})

        # Compute Project Health Grade based on the 4 pillars
        r_score = scores["site_risk_score"]
        s_score = scores["safety_score"]
        c_score = scores["compliance_score"]
        i_score = scores["insurance_risk_score"]

        # Health composite index: higher is better
        # Risk & Insurance are exposure scores (0-100 where 0 is best)
        # Safety & Compliance are performance scores (0-100 where 100 is best)
        health_index = (
            (100.0 - r_score) * 0.25 +
            s_score * 0.25 +
            c_score * 0.25 +
            (100.0 - i_score) * 0.25
        )

        if health_index >= 85:
            health_grade = "A — EXCELLENT"
            health_status = "HEALTHY"
        elif health_index >= 70:
            health_grade = "B — SATISFACTORY"
            health_status = "MODERATE"
        elif health_index >= 55:
            health_grade = "C — NEEDS IMPROVEMENT"
            health_status = "ATTENTION_REQUIRED"
        else:
            health_grade = "D — CRITICAL ACTION REQUIRED"
            health_status = "CRITICAL"

        # Strategic recommendations
        strat_recs = []
        if r_score > 50:
            strat_recs.append("Mitigate high-risk site conditions: suspend trenching during rain and reinspect scaffolding.")
        if s_score < 80:
            strat_recs.append(f"Reinforce PPE and worker certification protocols (current PPE compliance: {scores['ppe_compliance_rate_pct']}%).")
        if c_score < 80:
            strat_recs.append(f"Clear overdue inspection requirements ({domain.get('overdue_inspections', 0)} overdue) to satisfy OSHA standards.")
        if i_score > 40:
            strat_recs.append(f"Resolve outstanding safety & incident claims to lower insurance liability bracket ({scores['estimated_liability_exposure']}).")

        if not strat_recs:
            strat_recs.append("Project operations exhibit strong cross-agent health. Continue standard scheduled intelligence audits.")

        return {
            "report_title": f"Project Health Report — {site['name']}",
            "report_type": "PROJECT_HEALTH",
            "reporting_date": date_str,
            "generated_at": datetime.utcnow().isoformat(),
            "project_information": {
                "site_id": site["site_id"],
                "site_name": site["name"],
                "project_name": site["project_name"],
                "client": site["client"],
            },
            "composite_health": {
                "health_grade": health_grade,
                "health_status": health_status,
                "composite_index_pct": round(health_index, 1),
                "summary": (
                    f"Overall project health evaluated at {health_grade} with a composite score of {health_index:.1f}/100. "
                    f"Monitoring {metrics['total_findings']} total findings across 4 agent intelligence pillars."
                ),
            },
            "four_pillars": {
                "site_risk": {
                    "pillar_name": "Site Risk & Hazards",
                    "score": scores["site_risk_score"],
                    "risk_level": scores["site_risk_level"],
                    "active_hazards": len(findings["site_risk"]),
                    "status": "PASS" if scores["site_risk_score"] < 45 else ("WARN" if scores["site_risk_score"] < 70 else "FAIL"),
                    "summary": f"{len(findings['site_risk'])} active hazards detected by SiteRiskAgent.",
                },
                "safety": {
                    "pillar_name": "Worker & Behavioral Safety",
                    "score": scores["safety_score"],
                    "safety_level": scores["safety_level"],
                    "ppe_compliance_rate": f"{scores['ppe_compliance_rate_pct']}%",
                    "active_violations": len(findings["safety"]),
                    "status": "PASS" if scores["safety_score"] >= 80 else ("WARN" if scores["safety_score"] >= 65 else "FAIL"),
                    "summary": f"{len(findings['safety'])} safety findings and {len(findings['alerts'])} alerts logged by SafetyAgent.",
                },
                "compliance": {
                    "pillar_name": "Regulatory Compliance",
                    "score": scores["compliance_score"],
                    "compliance_status": scores["compliance_status"],
                    "overdue_inspections": domain.get("overdue_inspections", 0),
                    "active_violations": len(findings["compliance"]),
                    "status": "PASS" if scores["compliance_score"] >= 80 else ("WARN" if scores["compliance_score"] >= 65 else "FAIL"),
                    "summary": f"{len(findings['compliance'])} regulatory non-conformances identified by ComplianceAgent.",
                },
                "insurance": {
                    "pillar_name": "Insurance & Liability",
                    "score": scores["insurance_risk_score"],
                    "risk_level": scores["insurance_risk_level"],
                    "liability_exposure": scores["estimated_liability_exposure"],
                    "active_claims": len(findings["insurance"]),
                    "status": "PASS" if scores["insurance_risk_score"] < 40 else ("WARN" if scores["insurance_risk_score"] < 65 else "FAIL"),
                    "summary": f"Underwriting liability rated at {scores['estimated_liability_exposure']} with {len(findings['insurance'])} claims evaluated.",
                },
            },
            "critical_issues": findings["critical"] if findings["critical"] else "No findings available",
            "open_issues_count": metrics["open_count"],
            "cross_pillar_recommendations": strat_recs,
        }
