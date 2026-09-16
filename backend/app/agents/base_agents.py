"""
Agent Base Classes
==================
Phase 1.1: Interface/stub definitions for future AI agents.
Phase 1.2: These will be replaced with real LLM-powered implementations.

Agent Hierarchy:
  AgentOrchestrator
    ├── SiteRiskAgent       (Phase 1.2)
    ├── SafetyAgent         (Phase 2)
    ├── ComplianceAgent     (Phase 2)
    ├── InsuranceAgent      (Phase 3)
    └── ReportingAgent      (Phase 3)
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any


class BaseAgent(ABC):
    """Base class for all ACRIP AI agents."""

    def __init__(self, agent_id: str, name: str, version: str = "0.1.0"):
        self.agent_id = agent_id
        self.name = name
        self.version = version
        self.is_active = False
        self.last_run: Optional[datetime] = None

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with provided context."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if agent is ready to process."""
        pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "is_active": self.is_active,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "status": "active" if self.is_active else "inactive",
        }


class SiteRiskAgent(BaseAgent):
    """
    Site Risk Agent — Phase 1.2
    ============================
    Analyzes site activities, equipment, weather, and worker data
    using a deterministic RuleBasedRiskAnalyzer to automatically detect hazards,
    calculate multi-dimensional risk scores, and generate actionable recommendations.
    """

    def __init__(self):
        super().__init__(
            agent_id="site_risk_agent_v1",
            name="Site Risk Agent",
            version="1.0.0-phase1.2",
        )
        self.is_active = True
        from app.agents.site_risk_agent import RuleBasedRiskAnalyzer
        self.analyzer = RuleBasedRiskAnalyzer()

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.last_run = datetime.utcnow()
        return self.analyzer.analyze(context)

    async def health_check(self) -> bool:
        return True  # Active and functional in Phase 1.2


class SafetyAgent(BaseAgent):
    """
    Safety Agent — Phase 2.1
    ========================
    Worker safety compliance, PPE inspection foundation, training verification,
    and unsafe behavior detection using deterministic RuleBasedSafetyAnalyzer.
    """

    def __init__(self):
        super().__init__(
            agent_id="safety_agent_v1",
            name="Safety Agent",
            version="1.0.0-phase2.1",
        )
        self.is_active = True
        from app.agents.safety_agent import RuleBasedSafetyAnalyzer
        self.analyzer = RuleBasedSafetyAnalyzer()

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.last_run = datetime.utcnow()
        return self.analyzer.analyze(context)

    async def health_check(self) -> bool:
        return True


class ComplianceAgent(BaseAgent):
    """Compliance Agent — Milestone 3 (Regulatory compliance monitoring)"""

    def __init__(self):
        super().__init__("compliance_agent_v1", "Compliance Agent", "1.0.0-milestone3")
        self.is_active = True
        from app.services.compliance.engine import ComplianceAgent as RealComplianceAgent
        self._agent = RealComplianceAgent()

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.last_run = datetime.utcnow()
        return self._agent.evaluate(context)

    async def health_check(self) -> bool:
        return True


class InsuranceAgent(BaseAgent):
    """Insurance Agent — Milestone 3 (Insurance risk and claim analysis)"""

    def __init__(self):
        super().__init__("insurance_agent_v1", "Insurance Agent", "1.0.0-milestone3")
        self.is_active = True
        from app.services.insurance.engine import InsuranceAgent as RealInsuranceAgent
        self._agent = RealInsuranceAgent()

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.last_run = datetime.utcnow()
        return self._agent.assess_risk(context)

    async def health_check(self) -> bool:
        return True


class ReportingAgent(BaseAgent):
    """Reporting Agent — Phase 3 (Automated report generation)"""

    def __init__(self):
        super().__init__("reporting_agent_v1", "Reporting Agent", "0.1.0-stub")

    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Reporting Agent not yet implemented. Coming in Phase 3.")

    async def health_check(self) -> bool:
        return False


class AgentOrchestrator:
    """
    Agent Orchestrator
    ==================
    Coordinates all agents and manages their lifecycle.
    Phase 1.1: Stub — returns agent status only.
    Phase 1.2+: Will route data to appropriate agents.
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "site_risk": SiteRiskAgent(),
            "safety": SafetyAgent(),
            "compliance": ComplianceAgent(),
            "insurance": InsuranceAgent(),
            "reporting": ReportingAgent(),
        }

    def get_all_statuses(self) -> Dict[str, Any]:
        return {name: agent.get_status() for name, agent in self.agents.items()}

    async def run_agent(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        return await self.agents[agent_name].run(context)


# Global orchestrator instance
orchestrator = AgentOrchestrator()
