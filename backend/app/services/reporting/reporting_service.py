"""
Reporting Service — Milestone 4 Phase 4.1
=========================================
Orchestrates report generation, database persistence, retrieval,
and lifecycle operations for ACRIP.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from app.models.models import (
    GeneratedReport, ReportType, ReportStatus, Site, Project
)
from app.services.reporting.aggregator import ReportAggregationService
from app.services.reporting.generator import ReportGenerator


class ReportingService:
    """Enterprise reporting service managing multi-agent report lifecycles."""

    def __init__(self):
        self.aggregator = ReportAggregationService()
        self.generator = ReportGenerator()

    def generate_and_save_report(
        self,
        db: Session,
        site_id: str,
        report_type: ReportType = ReportType.DAILY_SITE,
        reporting_period_start: Optional[datetime] = None,
        reporting_period_end: Optional[datetime] = None,
        title: Optional[str] = None,
        created_by: str = "ReportingAgent",
        custom_context: Optional[Dict[str, Any]] = None,
    ) -> GeneratedReport:
        """
        Gathers live multi-agent intelligence, formats into specified report type,
        persists GeneratedReport record in database, and returns the entity.
        """
        # 1. Aggregate findings from all 4 agents
        aggregated = self.aggregator.aggregate_site_data(
            db=db if not custom_context else None,
            site_id=site_id,
            start_date=reporting_period_start,
            end_date=reporting_period_end,
            custom_context=custom_context,
        )

        site_info = aggregated["site"]
        project_id = site_info.get("project_id")

        # 2. Format into requested report type
        if report_type == ReportType.DAILY_SITE:
            content = self.generator.generate_daily_site_report(
                aggregated=aggregated,
                reporting_date=reporting_period_end or datetime.utcnow(),
            )
            default_title = f"Daily Site Report — {site_info['name']}"
            summary_text = content.get("overall_condition", {}).get("summary", "")
        elif report_type == ReportType.EXECUTIVE_SUMMARY:
            content = self.generator.generate_executive_risk_summary(
                aggregated=aggregated,
                reporting_date=reporting_period_end or datetime.utcnow(),
            )
            default_title = f"Executive Risk Summary — {site_info['name']}"
            summary_text = content.get("executive_narrative", "")
        elif report_type == ReportType.AUDIT_READY:
            content = self.generator.generate_audit_ready_report(
                aggregated=aggregated,
                start_date=reporting_period_start,
                end_date=reporting_period_end,
            )
            default_title = f"Audit-Ready Documentation — {site_info['name']}"
            summary_text = f"Audit dossier covering {aggregated['metrics']['total_findings']} records across all 4 agents."
        elif report_type == ReportType.PROJECT_HEALTH:
            content = self.generator.generate_project_health_report(
                aggregated=aggregated,
                reporting_date=reporting_period_end or datetime.utcnow(),
            )
            default_title = f"Project Health Assessment — {site_info['name']}"
            summary_text = content.get("composite_health", {}).get("summary", "")
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

        # 3. Create unique human-readable report code
        type_prefix = {
            ReportType.DAILY_SITE: "DSR",
            ReportType.EXECUTIVE_SUMMARY: "EXS",
            ReportType.AUDIT_READY: "AUD",
            ReportType.PROJECT_HEALTH: "PHR",
        }.get(report_type, "RPT")
        code = f"{type_prefix}-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # 4. Persist in database
        report_entity = GeneratedReport(
            id=str(uuid.uuid4()),
            report_id=code,
            site_id=site_id,
            project_id=project_id,
            report_type=report_type,
            title=title or default_title,
            reporting_period_start=reporting_period_start,
            reporting_period_end=reporting_period_end or datetime.utcnow(),
            generated_at=datetime.utcnow(),
            status=ReportStatus.COMPLETED,
            summary=summary_text,
            content=content,
            metrics=aggregated["metrics"],
            created_by=created_by,
        )

        db.add(report_entity)
        db.commit()
        db.refresh(report_entity)

        return report_entity

    def get_report(self, db: Session, report_id: str) -> Optional[GeneratedReport]:
        """Fetch report by primary key id or human-readable report_id."""
        return (
            db.query(GeneratedReport)
            .filter((GeneratedReport.id == report_id) | (GeneratedReport.report_id == report_id))
            .first()
        )

    def list_reports(
        self,
        db: Session,
        site_id: Optional[str] = None,
        project_id: Optional[str] = None,
        report_type: Optional[ReportType] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[GeneratedReport]:
        """Query and list persisted reports with optional filters."""
        query = db.query(GeneratedReport)
        if site_id:
            query = query.filter(GeneratedReport.site_id == site_id)
        if project_id:
            query = query.filter(GeneratedReport.project_id == project_id)
        if report_type:
            query = query.filter(GeneratedReport.report_type == report_type)

        return query.order_by(GeneratedReport.generated_at.desc()).offset(offset).limit(limit).all()

    def count_reports(
        self,
        db: Session,
        site_id: Optional[str] = None,
        report_type: Optional[ReportType] = None,
    ) -> int:
        """Count total reports matching criteria."""
        query = db.query(GeneratedReport)
        if site_id:
            query = query.filter(GeneratedReport.site_id == site_id)
        if report_type:
            query = query.filter(GeneratedReport.report_type == report_type)
        return query.count()

    def delete_report(self, db: Session, report_id: str) -> bool:
        """Delete report by id or report_id."""
        report = self.get_report(db, report_id)
        if not report:
            return False
        db.delete(report)
        db.commit()
        return True

    @staticmethod
    def get_available_report_types() -> List[Dict[str, Any]]:
        """List metadata and descriptions for all supported report types."""
        return [
            {
                "type": ReportType.DAILY_SITE.value,
                "name": "Daily Site Report",
                "description": "Comprehensive daily operational risk log including weather, hazards, safety violations, PPE compliance, and recommended actions.",
                "target_audience": "Site Managers, Safety Officers, Superintendents",
                "frequency": "Daily",
            },
            {
                "type": ReportType.EXECUTIVE_SUMMARY.value,
                "name": "Executive Risk Summary",
                "description": "High-level risk intelligence brief aggregating multi-pillar risk scores, critical open exposures, and strategic recommendations.",
                "target_audience": "Project Directors, Executives, Insurers",
                "frequency": "Weekly / On-Demand",
            },
            {
                "type": ReportType.AUDIT_READY.value,
                "name": "Audit-Ready Documentation",
                "description": "Traceable compliance audit dossier referencing OSHA/regulatory standards, finding IDs, evidence attachments, and verification states.",
                "target_audience": "Auditors, Regulators, Legal & Compliance",
                "frequency": "Monthly / Milestone Audit",
            },
            {
                "type": ReportType.PROJECT_HEALTH.value,
                "name": "Project Health Report",
                "description": "Holistic 4-pillar quadrant evaluation synthesizing Site Risk, Safety, Compliance, and Insurance into an actionable project health grade.",
                "target_audience": "Leadership, Risk Committees, Asset Owners",
                "frequency": "Weekly / Monthly",
            },
        ]
