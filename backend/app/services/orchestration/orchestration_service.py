"""
Agent Orchestration Service
===========================
Milestone 4 Phase 4.4: Agent Orchestration Engine

Coordinates:
    Site Risk Agent (M1)
    Safety Agent (M2)
    Compliance Agent (M3)
    Insurance Agent (M3)
            ↓ (Parallel Execution - Level 1)
    Construction Risk Intelligence Engine (Phase 4.2 - Level 2)
            ↓
    Reporting Agent (Phase 4.1 - Level 3)
            ↓
    Executive Dashboard (Phase 4.3)
"""

import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.session import SessionLocal
from app.models.models import (
    Site, Project, AgentOrchestrationRun, OrchestrationStatus,
    OrchestrationMode, ReportType
)
from app.schemas.schemas import (
    OrchestrationRequest, OrchestrationRunResponse, AgentExecutionStatus
)
from app.agents.site_risk_agent import site_risk_agent
from app.agents.safety_agent import safety_agent
from app.services.compliance.compliance_service import ComplianceService
from app.services.insurance.insurance_service import InsuranceService
from app.services.risk_intelligence.intelligence_service import RiskIntelligenceService
from app.services.reporting.reporting_service import ReportingService

compliance_service = ComplianceService()
insurance_service = InsuranceService()
risk_intelligence_service = RiskIntelligenceService()
reporting_service = ReportingService()
logger = logging.getLogger("acrip.orchestration")


class AgentDescriptor:
    """Metadata describing a registered agent in the ACRIP platform."""

    def __init__(
        self,
        name: str,
        display_name: str,
        agent_type: str,  # 'DOMAIN', 'AGGREGATOR', 'DOCUMENTATION'
        dependencies: List[str],
        timeout_seconds: int = 30,
        description: str = "",
    ):
        self.name = name
        self.display_name = display_name
        self.agent_type = agent_type
        self.dependencies = dependencies
        self.timeout_seconds = timeout_seconds
        self.description = description


class AgentRegistry:
    """Registry maintaining metadata and capabilities of all platform agents."""

    def __init__(self):
        self._agents: Dict[str, AgentDescriptor] = {
            "site_risk": AgentDescriptor(
                name="site_risk",
                display_name="Site Risk Agent",
                agent_type="DOMAIN",
                dependencies=[],
                timeout_seconds=30,
                description="Physical hazards, environmental conditions, and spatial risk scoring",
            ),
            "safety": AgentDescriptor(
                name="safety",
                display_name="Safety Agent",
                agent_type="DOMAIN",
                dependencies=[],
                timeout_seconds=30,
                description="Worker safety, PPE compliance, and real-time safety alerts",
            ),
            "compliance": AgentDescriptor(
                name="compliance",
                display_name="Compliance Agent",
                agent_type="DOMAIN",
                dependencies=[],
                timeout_seconds=30,
                description="Regulatory audit rules and statutory inspection tracking",
            ),
            "insurance": AgentDescriptor(
                name="insurance",
                display_name="Insurance Agent",
                agent_type="DOMAIN",
                dependencies=[],
                timeout_seconds=30,
                description="Actuarial exposure indexing and underwriting claim risks",
            ),
            "risk_intelligence": AgentDescriptor(
                name="risk_intelligence",
                display_name="Risk Intelligence Engine",
                agent_type="AGGREGATOR",
                dependencies=["site_risk", "safety", "compliance", "insurance"],
                timeout_seconds=45,
                description="Consolidated 4-pillar risk scoring, pattern detection, incident predictions, and recommendations",
            ),
            "reporting": AgentDescriptor(
                name="reporting",
                display_name="Reporting Agent",
                agent_type="DOCUMENTATION",
                dependencies=["risk_intelligence"],
                timeout_seconds=45,
                description="Structured audit-ready report compilation and distribution",
            ),
        }

    def get_agent(self, name: str) -> Optional[AgentDescriptor]:
        return self._agents.get(name)

    def list_agents(self) -> List[AgentDescriptor]:
        return list(self._agents.values())

    def get_domain_agent_names(self) -> List[str]:
        return [k for k, v in self._agents.items() if v.agent_type == "DOMAIN"]


class OrchestrationService:
    """
    Central Orchestration Service managing parallel execution, dependency chaining,
    failure isolation, and persistence across ACRIP agents.
    """

    def __init__(self):
        self.registry = AgentRegistry()
        # In-memory active runs dictionary: {site_id: (execution_id, start_time)}
        self._active_runs: Dict[str, Tuple[str, datetime]] = {}

    def _acquire_run_lock(self, site_id: str, execution_id: str) -> bool:
        """Check for active running execution on the same site within last 30s."""
        now = datetime.utcnow()
        if site_id in self._active_runs:
            active_id, start_time = self._active_runs[site_id]
            if (now - start_time) < timedelta(seconds=30):
                return False
        self._active_runs[site_id] = (execution_id, now)
        return True

    def _release_run_lock(self, site_id: str, execution_id: str):
        """Release the run lock for a site."""
        if site_id in self._active_runs:
            active_id, _ = self._active_runs[site_id]
            if active_id == execution_id:
                self._active_runs.pop(site_id, None)

    # ── Level 1: Domain Agent Worker Callables ────────────────────────────

    def _execute_site_risk(self, site_id: str) -> Dict[str, Any]:
        """Execute Site Risk Agent in isolated thread DB session."""
        thread_db = SessionLocal()
        try:
            res = site_risk_agent.analyze_and_persist(db=thread_db, site_id=site_id)
            score = res.get("overall_score", res.get("risk_score", 0.0))
            hazards = res.get("hazards", [])
            hazards_count = len(hazards)
            return {
                "summary": f"Analyzed site hazards: score {score:.1f}, {hazards_count} active hazards detected.",
                "overall_score": score,
                "hazards_count": hazards_count,
                "hazards": hazards,
            }
        finally:
            thread_db.close()

    def _execute_safety(self, site_id: str) -> Dict[str, Any]:
        """Execute Safety Agent in isolated thread DB session."""
        thread_db = SessionLocal()
        try:
            res = safety_agent.analyze_and_persist(db=thread_db, site_id=site_id)
            score = res.get("overall_safety_score", 0.0)
            violations_count = res.get("violation_count", 0)
            return {
                "summary": f"Analyzed worker safety: safety score {score:.1f}, {violations_count} findings.",
                "safety_score": score,
                "violations_count": violations_count,
            }
        finally:
            thread_db.close()

    def _execute_compliance(self, site_id: str, is_simulation: bool = False) -> Dict[str, Any]:
        """Execute Compliance Agent in isolated thread DB session."""
        thread_db = SessionLocal()
        try:
            res = compliance_service.analyze_site_compliance(
                db=thread_db, site_id=site_id, is_simulation=is_simulation
            )
            score = getattr(res, "compliance_score", 0.0)
            status_val = getattr(res, "compliance_status", "UNKNOWN")
            status_str = status_val.value if hasattr(status_val, "value") else str(status_val)
            overdue = getattr(res, "overdue_inspections", 0)
            return {
                "summary": f"Compliance audit: {score:.1f}% compliance, status {status_str}, {overdue} overdue inspections.",
                "compliance_score": score,
                "status": status_str,
                "overdue_inspections": overdue,
            }
        finally:
            thread_db.close()

    def _execute_insurance(self, site_id: str, is_simulation: bool = False) -> Dict[str, Any]:
        """Execute Insurance Agent in isolated thread DB session."""
        thread_db = SessionLocal()
        try:
            res = insurance_service.assess_site_insurance(
                db=thread_db, site_id=site_id, is_simulation=is_simulation
            )
            score = getattr(res, "insurance_risk_score", 0.0)
            exposure = getattr(res, "exposure_index", 1.0)
            return {
                "summary": f"Underwriting assessment: risk score {score:.1f}, exposure multiplier {exposure:.2f}x.",
                "insurance_risk_score": score,
                "exposure_index": exposure,
            }
        finally:
            thread_db.close()

    # ── Main Orchestration Workflow ───────────────────────────────────────

    def execute_orchestration(
        self,
        db: Session,
        request: OrchestrationRequest,
        created_by: str = "AgentOrchestrator",
    ) -> OrchestrationRunResponse:
        """
        Execute cross-agent orchestration workflow across Level 1 (Domain),
        Level 2 (Risk Intelligence Engine), and Level 3 (Reporting Agent).
        """
        site = db.query(Site).filter(Site.id == request.site_id).first()
        if not site:
            raise ValueError(f"Site '{request.site_id}' not found.")

        site_id_val = str(site.id)
        project_id_val = str(site.project_id) if site.project_id else request.project_id

        # Determine execution mode and target domain agents
        mode_str = request.mode or OrchestrationMode.FULL_ANALYSIS.value
        all_domain_agents = self.registry.get_domain_agent_names()

        if mode_str == OrchestrationMode.FULL_ANALYSIS.value:
            target_domain_agents = all_domain_agents
        elif mode_str == OrchestrationMode.TARGETED_ANALYSIS.value:
            requested = request.agents or all_domain_agents
            target_domain_agents = [a for a in requested if a in all_domain_agents]
        elif mode_str == OrchestrationMode.REFRESH.value:
            # Skip domain agent re-execution, refresh Risk Intelligence directly
            target_domain_agents = []
        elif mode_str == OrchestrationMode.REPORT_REFRESH.value:
            # Skip domain agents and Risk Intelligence, run reporting only
            target_domain_agents = []
        else:
            target_domain_agents = all_domain_agents

        # Execution ID & Run Record Initialization
        execution_id = f"ORCH-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Idempotency / active-run protection
        if not self._acquire_run_lock(site_id_val, execution_id):
            active_info = self._active_runs.get(site_id_val)
            active_id = active_info[0] if active_info else "active"
            raise ValueError(
                f"An active orchestration run ({active_id}) is currently in progress for site '{site_id_val}'. "
                "Please wait for it to complete."
            )

        start_time = datetime.utcnow()
        t0 = time.time()

        agent_statuses: Dict[str, Dict[str, Any]] = {}
        warnings: List[str] = []
        errors: List[str] = []

        # Pre-populate requested agent statuses
        all_planned = list(target_domain_agents)
        if mode_str != OrchestrationMode.REPORT_REFRESH.value:
            all_planned.append("risk_intelligence")
        if request.generate_report or mode_str == OrchestrationMode.REPORT_REFRESH.value:
            all_planned.append("reporting")

        for a_name in all_planned:
            agent_statuses[a_name] = {
                "agent_name": a_name,
                "status": OrchestrationStatus.PENDING.value,
                "duration_ms": 0.0,
                "error": None,
                "message": None,
                "output_summary": None,
            }

        # Create persistent DB record
        run_record = AgentOrchestrationRun(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            site_id=site_id_val,
            project_id=project_id_val,
            status=OrchestrationStatus.RUNNING,
            execution_mode=OrchestrationMode(mode_str),
            requested_agents=all_planned,
            agent_statuses=agent_statuses,
            created_by=created_by,
            started_at=start_time,
        )
        db.add(run_record)
        db.commit()
        db.refresh(run_record)

        try:
            # ── LEVEL 1: Parallel Domain Agent Execution ──────────────────
            successful_domain_agents: List[str] = []

            if target_domain_agents:
                logger.info(f"[{execution_id}] Starting parallel execution of domain agents: {target_domain_agents}")
                agent_dispatchers = {
                    "site_risk": lambda: self._execute_site_risk(site_id_val),
                    "safety": lambda: self._execute_safety(site_id_val),
                    "compliance": lambda: self._execute_compliance(site_id_val, is_simulation=bool(request.is_simulation)),
                    "insurance": lambda: self._execute_insurance(site_id_val, is_simulation=bool(request.is_simulation)),
                }

                with ThreadPoolExecutor(max_workers=min(4, len(target_domain_agents))) as executor:
                    future_to_agent = {}
                    for a_name in target_domain_agents:
                        dispatcher = agent_dispatchers.get(a_name)
                        if dispatcher:
                            agent_statuses[a_name]["status"] = OrchestrationStatus.RUNNING.value
                            future = executor.submit(dispatcher)
                            future_to_agent[future] = (a_name, time.time())

                    for future in as_completed(future_to_agent):
                        a_name, a_start = future_to_agent[future]
                        a_duration = (time.time() - a_start) * 1000
                        try:
                            result_data = future.result(timeout=45)
                            agent_statuses[a_name]["status"] = OrchestrationStatus.COMPLETED.value
                            agent_statuses[a_name]["duration_ms"] = round(a_duration, 1)
                            agent_statuses[a_name]["message"] = result_data.get("summary", "Analysis completed.")
                            agent_statuses[a_name]["output_summary"] = result_data
                            successful_domain_agents.append(a_name)
                            logger.info(f"[{execution_id}] Agent '{a_name}' COMPLETED in {a_duration:.1f}ms")
                        except Exception as e:
                            agent_statuses[a_name]["status"] = OrchestrationStatus.FAILED.value
                            agent_statuses[a_name]["duration_ms"] = round(a_duration, 1)
                            agent_statuses[a_name]["error"] = str(e)
                            agent_statuses[a_name]["message"] = f"Execution failed: {str(e)}"
                            errors.append(f"Domain agent '{a_name}' failed: {str(e)}")
                            warnings.append(f"Agent '{a_name}' failed; continuing workflow with remaining agents.")
                            logger.error(f"[{execution_id}] Agent '{a_name}' FAILED: {str(e)}", exc_info=True)

            # ── LEVEL 2: Risk Intelligence Engine Execution ───────────────
            rki_id: Optional[str] = None

            if mode_str != OrchestrationMode.REPORT_REFRESH.value:
                # Failure isolation check: can Risk Intelligence proceed?
                if target_domain_agents and len(successful_domain_agents) == 0:
                    # Every requested domain agent failed!
                    agent_statuses["risk_intelligence"]["status"] = OrchestrationStatus.SKIPPED.value
                    agent_statuses["risk_intelligence"]["message"] = "Skipped because all upstream domain agents failed."
                    warnings.append("Risk Intelligence Engine skipped because all upstream domain agents failed.")
                    logger.warning(f"[{execution_id}] Risk Intelligence skipped: 0 domain agents succeeded.")
                else:
                    # Proceed with Risk Intelligence
                    agent_statuses["risk_intelligence"]["status"] = OrchestrationStatus.RUNNING.value
                    rki_start = time.time()
                    try:
                        rki_assessment = risk_intelligence_service.analyze_and_save(
                            db=db,
                            site_id=site_id_val,
                            project_id=project_id_val,
                            time_window_days=30,
                            created_by=f"Orchestration-{execution_id}",
                        )
                        rki_duration = (time.time() - rki_start) * 1000
                        rki_id = rki_assessment.intelligence_id
                        agent_statuses["risk_intelligence"]["status"] = OrchestrationStatus.COMPLETED.value
                        agent_statuses["risk_intelligence"]["duration_ms"] = round(rki_duration, 1)
                        agent_statuses["risk_intelligence"]["message"] = (
                            f"Consolidated risk assessment generated: overall score {rki_assessment.overall_risk_score:.1f}, "
                            f"{len(rki_assessment.recurring_patterns or [])} patterns, "
                            f"{len(rki_assessment.potential_incidents or [])} predictions."
                        )
                        agent_statuses["risk_intelligence"]["output_summary"] = {
                            "intelligence_id": rki_id,
                            "overall_risk_score": rki_assessment.overall_risk_score,
                            "risk_level": rki_assessment.risk_level,
                            "patterns_count": len(rki_assessment.recurring_patterns or []),
                            "predictions_count": len(rki_assessment.potential_incidents or []),
                        }
                        logger.info(f"[{execution_id}] Risk Intelligence COMPLETED: score {rki_assessment.overall_risk_score}")
                    except Exception as e:
                        rki_duration = (time.time() - rki_start) * 1000
                        agent_statuses["risk_intelligence"]["status"] = OrchestrationStatus.FAILED.value
                        agent_statuses["risk_intelligence"]["duration_ms"] = round(rki_duration, 1)
                        agent_statuses["risk_intelligence"]["error"] = str(e)
                        agent_statuses["risk_intelligence"]["message"] = f"Risk Intelligence failed: {str(e)}"
                        errors.append(f"Risk Intelligence Engine failed: {str(e)}")
                        logger.error(f"[{execution_id}] Risk Intelligence FAILED: {str(e)}", exc_info=True)

            # ── LEVEL 3: Reporting Agent Execution ─────────────────────────
            rep_id: Optional[str] = None

            if "reporting" in agent_statuses:
                if (
                    agent_statuses.get("risk_intelligence", {}).get("status") == OrchestrationStatus.COMPLETED.value
                    or mode_str == OrchestrationMode.REPORT_REFRESH.value
                ):
                    agent_statuses["reporting"]["status"] = OrchestrationStatus.RUNNING.value
                    rep_start = time.time()
                    try:
                        rep_type = request.report_type or ReportType.EXECUTIVE_SUMMARY
                        report = reporting_service.generate_and_save_report(
                            db=db,
                            site_id=site_id_val,
                            report_type=rep_type,
                            created_by=f"Orchestration-{execution_id}",
                        )
                        rep_duration = (time.time() - rep_start) * 1000
                        rep_id = report.report_id
                        agent_statuses["reporting"]["status"] = OrchestrationStatus.COMPLETED.value
                        agent_statuses["reporting"]["duration_ms"] = round(rep_duration, 1)
                        agent_statuses["reporting"]["message"] = f"Report '{report.title}' successfully compiled and persisted."
                        agent_statuses["reporting"]["output_summary"] = {
                            "report_id": rep_id,
                            "report_type": report.report_type.value,
                            "title": report.title,
                        }
                        logger.info(f"[{execution_id}] Reporting Agent COMPLETED: {rep_id}")
                    except Exception as e:
                        rep_duration = (time.time() - rep_start) * 1000
                        agent_statuses["reporting"]["status"] = OrchestrationStatus.FAILED.value
                        agent_statuses["reporting"]["duration_ms"] = round(rep_duration, 1)
                        agent_statuses["reporting"]["error"] = str(e)
                        agent_statuses["reporting"]["message"] = f"Report generation failed: {str(e)}"
                        errors.append(f"Reporting Agent failed: {str(e)}")
                        logger.error(f"[{execution_id}] Reporting Agent FAILED: {str(e)}", exc_info=True)
                else:
                    agent_statuses["reporting"]["status"] = OrchestrationStatus.SKIPPED.value
                    agent_statuses["reporting"]["message"] = "Skipped because Risk Intelligence did not complete."

            # ── Final Status Evaluation ───────────────────────────────────
            has_failures = any(
                st.get("status") == OrchestrationStatus.FAILED.value
                for st in agent_statuses.values()
            )
            has_successes = any(
                st.get("status") == OrchestrationStatus.COMPLETED.value
                for st in agent_statuses.values()
            )

            if not has_failures:
                final_status = OrchestrationStatus.COMPLETED
            elif has_successes:
                final_status = OrchestrationStatus.PARTIAL
                warnings.append("Orchestration completed partially with one or more agent failures.")
            else:
                final_status = OrchestrationStatus.FAILED

            completed_at = datetime.utcnow()
            total_duration_ms = (time.time() - t0) * 1000

            # Update DB Run Record
            run_record.status = final_status
            run_record.agent_statuses = agent_statuses
            run_record.risk_intelligence_id = rki_id
            run_record.report_id = rep_id
            run_record.duration_ms = round(total_duration_ms, 1)
            run_record.warnings = warnings
            run_record.errors = errors
            run_record.completed_at = completed_at

            db.commit()
            db.refresh(run_record)

            return OrchestrationRunResponse.model_validate(run_record)

        finally:
            self._release_run_lock(request.site_id, execution_id)

    # ── Query Methods ─────────────────────────────────────────────────────

    def get_execution(self, db: Session, execution_id: str) -> OrchestrationRunResponse:
        """Get execution details by execution ID."""
        run = (
            db.query(AgentOrchestrationRun)
            .filter(AgentOrchestrationRun.execution_id == execution_id)
            .first()
        )
        if not run:
            raise ValueError(f"Orchestration run '{execution_id}' not found.")
        return OrchestrationRunResponse.model_validate(run)

    def get_latest_site_execution(self, db: Session, site_id: str) -> Optional[OrchestrationRunResponse]:
        """Get the latest orchestration run for a site."""
        run = (
            db.query(AgentOrchestrationRun)
            .filter(AgentOrchestrationRun.site_id == site_id)
            .order_by(desc(AgentOrchestrationRun.started_at))
            .first()
        )
        if not run:
            return None
        return OrchestrationRunResponse.model_validate(run)

    def list_site_executions(
        self, db: Session, site_id: str, limit: int = 20, offset: int = 0
    ) -> Tuple[List[OrchestrationRunResponse], int]:
        """List historical orchestration runs for a site."""
        query = db.query(AgentOrchestrationRun).filter(AgentOrchestrationRun.site_id == site_id)
        total = query.count()
        runs = query.order_by(desc(AgentOrchestrationRun.started_at)).offset(offset).limit(limit).all()
        return [OrchestrationRunResponse.model_validate(r) for r in runs], total


orchestration_service = OrchestrationService()
