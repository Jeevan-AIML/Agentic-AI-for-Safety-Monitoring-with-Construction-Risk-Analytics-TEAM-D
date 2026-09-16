"""Configured Construction Regulatory Rules Catalog.

Deterministic construction safety and regulatory standards referencing:
- OSHA 29 CFR 1926 (Safety and Health Regulations for Construction)
- Indian Standards (IS 4081, IS 3696)
- ISO 45001 (Occupational Health & Safety Management Systems)

All rules are deterministic, auditable, and clearly distinguished from demo simulations.
"""

from typing import List, Dict, Any
from app.models.models import ComplianceRuleCategory, RiskCategory


DEFAULT_COMPLIANCE_RULES: List[Dict[str, Any]] = [
    {
        "rule_id": "R-OSHA-1926.95",
        "standard_ref": "OSHA 1926.95",
        "title": "Mandatory Personal Protective Equipment (PPE) Compliance",
        "category": ComplianceRuleCategory.PPE,
        "requirement": (
            "Protective equipment, including personal protective equipment for eyes, face, head, "
            "and extremities, protective clothing, respiratory devices, and protective shields, "
            "shall be provided, used, and maintained in a sanitary and reliable condition."
        ),
        "applicable_activity": "general_construction",
        "applicable_zone": "all_zones",
        "severity": RiskCategory.HIGH,
        "remediation_recommendation": (
            "Immediately halt worker operations without required PPE (Hard Hat, High-Vis Vest, "
            "Safety Boots, Eye Protection). Reissue certified gear prior to work recommencement."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-OSHA-1926.451",
        "standard_ref": "OSHA 1926.451",
        "title": "Scaffolding Guardrails, Toe-boards, and Fall Arrest Systems",
        "category": ComplianceRuleCategory.SCAFFOLDING_SAFETY,
        "requirement": (
            "Each employee on a scaffold more than 10 feet (3.1 m) above a lower level shall be "
            "protected from falling to that lower level by guardrail systems or personal fall arrest systems. "
            "Platforms shall be fully planked and equipped with mid-rails and toe-boards."
        ),
        "applicable_activity": "scaffolding",
        "applicable_zone": "Zone B — Structural Works",
        "severity": RiskCategory.CRITICAL,
        "remediation_recommendation": (
            "Issue immediate Stop-Work Order on unshielded scaffold bays. Install OSHA-compliant "
            "top rails (42 inches +/- 3 inches), mid-rails, and anchor personal fall arrest harnesses."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-OSHA-1926.651",
        "standard_ref": "OSHA 1926.651",
        "title": "Excavation Wall Protection and Shoring Mandate",
        "category": ComplianceRuleCategory.EXCAVATION_SAFETY,
        "requirement": (
            "Each employee in an excavation 5 feet (1.5 m) or deeper shall be protected from cave-ins "
            "by an adequate protective system (sloping, benching, shield, or shoring). Daily pre-entry "
            "inspections by a competent person are mandatory."
        ),
        "applicable_activity": "excavation",
        "applicable_zone": "Zone A — Deep Excavation Pit",
        "severity": RiskCategory.CRITICAL,
        "remediation_recommendation": (
            "Evacuate excavation trench immediately. Deploy certified hydraulic shoring or trench boxes. "
            "Require written geotechnical sign-off from competent safety supervisor prior to re-entry."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-OSHA-1926.403",
        "standard_ref": "OSHA 1926.403",
        "title": "Temporary Electrical Distribution, Enclosures, and GFCI Verification",
        "category": ComplianceRuleCategory.ELECTRICAL_SAFETY,
        "requirement": (
            "All temporary 120-volt, single-phase, 15- and 20-ampere receptacle outlets shall have approved "
            "ground-fault circuit interrupters (GFCI) for personnel protection. Distribution boards must be weatherproof."
        ),
        "applicable_activity": "electrical_work",
        "applicable_zone": "Zone C — Utility Hub",
        "severity": RiskCategory.CRITICAL,
        "remediation_recommendation": (
            "De-energize ungrounded circuits. Install certified GFCI breakers and inspect temporary cables "
            "for mechanical abrasion, moisture ingress, or lack of water-tight seals."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-ISO-45001-7.2",
        "standard_ref": "ISO 45001:2018 Cl. 7.2",
        "title": "Operator Competency and Heavy Machinery Verification",
        "category": ComplianceRuleCategory.EQUIPMENT_CERTIFICATION,
        "requirement": (
            "The organization shall ensure that workers are competent (including the ability to identify hazards) "
            "on the basis of appropriate education, training, or experience prior to operating powered mobile equipment."
        ),
        "applicable_activity": "material_handling",
        "applicable_zone": "Zone C — Tower Crane Radius",
        "severity": RiskCategory.CRITICAL,
        "remediation_recommendation": (
            "Lockout / Tagout (LOTO) heavy equipment operated by unverified personnel. Cross-check "
            "operator third-party license and competency certification records in platform register."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-IS-4081-1986",
        "standard_ref": "IS 4081:1986",
        "title": "Indian Standard Safety Code for Blasting and Drilling Operations",
        "category": ComplianceRuleCategory.EXCAVATION_SAFETY,
        "requirement": (
            "Rigid exclusion perimeters of minimum 200m radius shall be established during mechanical drilling, "
            "piling, or explosive blasting. Dedicated sirens and red warning flags must be actively deployed."
        ),
        "applicable_activity": "excavation",
        "applicable_zone": "Zone A — Deep Excavation Pit",
        "severity": RiskCategory.HIGH,
        "remediation_recommendation": (
            "Evacuate non-essential personnel to designated muster station. Verify acoustic warning alarm "
            "and secure physical barriers with posted sentries."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-OSHA-1926.150",
        "standard_ref": "OSHA 1926.150",
        "title": "Site Fire Protection & Portable Extinguisher Deployment",
        "category": ComplianceRuleCategory.EMERGENCY_DOCUMENTATION,
        "requirement": (
            "A fire extinguisher, rated not less than 2A, shall be provided for each 3,000 square feet of the "
            "protected building area. For hot work or fuel storage, minimum 10B:C extinguisher must be within 50 feet."
        ),
        "applicable_activity": "welding",
        "applicable_zone": "Zone D — Material Yard",
        "severity": RiskCategory.MEDIUM,
        "remediation_recommendation": (
            "Position twin 10kg ABC dry-chemical extinguishers at hot-work perimeter. Designate continuous "
            "fire-watch guard during and for 30 minutes post welding operations."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-DOC-001",
        "standard_ref": "OSHA 1926.21(b)(2)",
        "title": "Daily Pre-Shift Toolbox Talk and Safety Briefing Documentation",
        "category": ComplianceRuleCategory.EMERGENCY_DOCUMENTATION,
        "requirement": (
            "The employer shall instruct each employee in the recognition and avoidance of unsafe conditions "
            "and regulations applicable to his work environment. Daily attendance logs must be documented."
        ),
        "applicable_activity": "general_construction",
        "applicable_zone": "all_zones",
        "severity": RiskCategory.MEDIUM,
        "remediation_recommendation": (
            "Conduct pre-shift briefing with supervisor and record digital signatures on platform log "
            "before clearing worker access gates."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-IS-3696-PART1",
        "standard_ref": "IS 3696 (Part 1): 1987",
        "title": "Safety Code of Scaffolds and Ladders — Base Stability and Sole Plates",
        "category": ComplianceRuleCategory.SCAFFOLDING_SAFETY,
        "requirement": (
            "Scaffold uprights (standards) shall be set on firm foundations with sound timber sole plates "
            "of minimum 38 mm thickness, adequately bedded to prevent differential settlement."
        ),
        "applicable_activity": "scaffolding",
        "applicable_zone": "Zone B — Structural Works",
        "severity": RiskCategory.HIGH,
        "remediation_recommendation": (
            "Install screw jacks and hardwood sole plates under standards. Re-level ledger horizontal tubes "
            "and inspect ledger ties to structural columns."
        ),
        "is_active": True,
    },
    {
        "rule_id": "R-OSHA-1926.501",
        "standard_ref": "OSHA 1926.501",
        "title": "Roof Edge and Floor Hole Unprotected Edge Fall Protection",
        "category": ComplianceRuleCategory.SCAFFOLDING_SAFETY,
        "requirement": (
            "Each employee on a walking/working surface with an unprotected side or edge which is 6 feet (1.8 m) "
            "or more above a lower level shall be protected from falling by the use of guardrail systems, safety net "
            "systems, or personal fall arrest systems."
        ),
        "applicable_activity": "roofing",
        "applicable_zone": "Zone B — Structural Works",
        "severity": RiskCategory.CRITICAL,
        "remediation_recommendation": (
            "Erect rigid perimeter cable barriers or install 5,000-lb rated dorsal D-ring horizontal lifelines. "
            "Bar access to floor holes and elevator shafts with secured, marked covers."
        ),
        "is_active": True,
    }
]
