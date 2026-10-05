"""
Reporting Agent — Milestone 4 Phase 4.1
=======================================
Intelligent Multi-Agent Reporting & Synthesis Engine.
Collects, normalizes, and aggregates findings from Site Risk Agent,
Safety Agent, Compliance Agent, and Insurance Agent to generate
auditable, executive, operational, and health reports.

Architecture:
    ReportingAgent (BaseAgent)
        ↓
    ReportAggregationService
        ↓
    Normalized Findings from (SiteRisk, Safety, Compliance, Insurance)
        ↓
    ReportGenerator
        ↓
    Daily / Executive / Audit / Project Health Reports
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import ReportType
from app.services.reporting.aggregator import ReportAggregationService
from app.services.reporting.generator import ReportGenerator
from app.services.reporting.reporting_service import ReportingService


class ReportingAgent:
    """
    Reporting Agent — Milestone 4 Phase 4.1
    Cross-pillar intelligence aggregator and report synthesis agent.
    """

    def __init__(self):
        self.agent_id = "reporting_agent_v1"
        self.name = "Reporting Agent"
        self.version = "1.0.0-phase4.1"
        self.is_active = True
        self.last_run: Optional[datetime] = None

        self.aggregator = ReportAggregationService()
        self.generator = ReportGenerator()
        self.service = ReportingService()

    async def health_check(self) -> bool:
        """Check if Reporting Agent is active and ready."""
        return True

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "is_active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "status": "active" if self.is_active else "inactive",
        }

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute report synthesis based on context.
        Context can contain:
          - 'site_id': Target site
          - 'report_type': 'DAILY_SITE' | 'EXECUTIVE_SUMMARY' | 'AUDIT_READY' | 'PROJECT_HEALTH'
          - 'hazards', 'safety_findings', 'compliance_findings', 'insurance_claims'
        """
        self.last_run = datetime.utcnow()
        report_type_str = context.get("report_type", "DAILY_SITE").upper()

        try:
            r_type = ReportType(report_type_str)
        except ValueError:
            r_type = ReportType.DAILY_SITE

        # Aggregate findings
        aggregated = self.aggregator.aggregate_site_data(
            custom_context=context,
            site_id=context.get("site_id", "SITE-001"),
        )

        # Generate report
        if r_type == ReportType.DAILY_SITE:
            result = self.generator.generate_daily_site_report(aggregated)
        elif r_type == ReportType.EXECUTIVE_SUMMARY:
            result = self.generator.generate_executive_risk_summary(aggregated)
        elif r_type == ReportType.AUDIT_READY:
            result = self.generator.generate_audit_ready_report(aggregated)
        elif r_type == ReportType.PROJECT_HEALTH:
            result = self.generator.generate_project_health_report(aggregated)
        else:
            result = self.generator.generate_daily_site_report(aggregated)

        result["agent_metadata"] = {
            "generated_by": self.name,
            "agent_id": self.agent_id,
            "version": self.version,
            "timestamp": self.last_run.isoformat(),
        }

        return result

    def generate_report(
        self,
        db: Session,
        site_id: str,
        report_type: ReportType = ReportType.DAILY_SITE,
        reporting_period_start: Optional[datetime] = None,
        reporting_period_end: Optional[datetime] = None,
        title: Optional[str] = None,
        created_by: str = "ReportingAgent",
    ) -> Dict[str, Any]:
        """Direct database-driven generation and persistence helper."""
        self.last_run = datetime.utcnow()
        report_entity = self.service.generate_and_save_report(
            db=db,
            site_id=site_id,
            report_type=report_type,
            reporting_period_start=reporting_period_start,
            reporting_period_end=reporting_period_end,
            title=title,
            created_by=created_by,
        )
        return {
            "id": report_entity.id,
            "report_id": report_entity.report_id,
            "report_type": report_entity.report_type.value,
            "title": report_entity.title,
            "generated_at": report_entity.generated_at.isoformat(),
            "status": report_entity.status.value,
            "content": report_entity.content,
            "metrics": report_entity.metrics,
        }


# Singleton instance
reporting_agent = ReportingAgent()
