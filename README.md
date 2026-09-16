# ACRIP — Agentic Construction Risk Intelligence Platform

> **Milestone 1 (Complete) + Milestone 2 Phase 2.1, 2.2 & 2.3 (Complete & Hardened)**
> Worker Safety Intelligence, CV PPE Detection, Live Worker Safety Monitoring & Autonomous Safety Agent Engine

ACRIP is an enterprise-grade construction safety and risk intelligence platform. In Milestone 1, it delivers deterministic site risk intelligence, hazard lifecycles, and risk scoring. In Milestone 2 Phase 2.1, it integrates a dedicated **Safety Agent** for worker safety compliance and certifications. In Milestone 2 Phase 2.2, it introduces **Computer Vision PPE Compliance Detection** for construction image analysis (`HARD_HAT`, `SAFETY_VEST`, `SAFETY_GOGGLES`), worker localization, visual bounding box overlays, confidence thresholding, deterministic compliance evaluation, and DB cross-verification. In Milestone 2 Phase 2.3, it introduces **Worker Safety Monitoring** for live worker activity tracking, high-risk zone exposure, time-in-zone dwell thresholds, active hazard proximity, heavy equipment standoff boundaries, zone overcrowding density, and deterministic safety status calculations (`SAFE`, `WARNING`, `HIGH_RISK`, `CRITICAL`).

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────────────────────┐
                               │             React + TypeScript UI              │
                               │   (Dashboard, Risk Monitoring, Hazard Modals)  │
                               └───────────────────────┬────────────────────────┘
                                                       │ REST API (JWT Bearer)
                                                       ▼
                               ┌────────────────────────────────────────────────┐
                               │             FastAPI Backend Layer              │
                               │  (/api/v1/auth, /sites, /risk, /hazards, etc.) │
                               └───────────────────────┬────────────────────────┘
                                                       │
                     ┌─────────────────────────────────┴─────────────────────────────────┐
                     ▼                                                                   ▼
       ┌───────────────────────────┐                                       ┌───────────────────────────┐
       │      SiteRiskAgent        │                                       │   Database Persistence    │
       │   (Autonomous Agent)      │                                       │  (SQLite / PostgreSQL)    │
       └─────────────┬─────────────┘                                       │  Users, Projects, Sites,  │
                     ▼                                                     │  Hazards, RiskScores,     │
       ┌───────────────────────────┐                                       │  Notifications, Equipment │
       │     BaseRiskAnalyzer      │                                       └───────────────────────────┘
       │  (Extensible Analyzer)    │
       └─────────────┬─────────────┘
                     ▼
       ┌───────────────────────────┐
       │   RuleBasedRiskAnalyzer   │
       │  (10 Deterministic Rules) │
       └───────────────────────────┘
```

> **IMPORTANT ARCHITECTURAL NOTE:**
> - **CURRENT IMPLEMENTATION:** Fully explainable, deterministic rule-based risk engine (`detection_source: RULE_ENGINE`). No random outputs, no hallucinated results, 100% reproducible and auditable for safety compliance.
> - **FUTURE CAPABILITIES:** Extensible agent interface (`BaseRiskAnalyzer`) designed for future integration with multimodal LLMs, sensor telemetry streams, and computer vision / edge camera models in subsequent milestones.

---

## ⚙️ Technology Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TanStack React Query v5, Recharts, Framer Motion, Lucide Icons, React Hot Toast
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy ORM, Pydantic v2 Settings & Models, SQLite / PostgreSQL, Pytest, Uvicorn
- **Security & RBAC:** JWT (HS256), Passlib (Bcrypt), Strict role-based access control (Super Admin, Project Manager, Site Manager, Safety Officer, Viewer)

---

## 🚀 Quick Start & How to Run

### Prerequisites
- Node.js 18+
- Python 3.11+
- pip & npm

### 1. Start the Backend
```powershell
cd "Agentic AI/ACRIP/backend"
python -m venv venv                # Optional virtualenv
.\venv\Scripts\activate            # Activate virtualenv on Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Documentation (Swagger): **http://localhost:8000/docs**
- Health check: **http://localhost:8000/health**

### 2. Start the Frontend
```powershell
cd "Agentic AI/ACRIP/frontend"
npm install
npm run dev
```
- Web Application: **http://localhost:5173**

---

## 🔐 Demo Accounts & RBAC Matrix

| Role | Email | Password | Permissions |
|------|-------|----------|-------------|
| **Super Admin** | `admin@acriplatform.com` | `Admin@123` | Full system access, user administration, all sites & projects |
| **Project Manager** | `manager@acriplatform.com` | `Manager@123` | Project & site oversight, risk analysis, hazard tracking |
| **Site Manager** | `site.manager@acriplatform.com` | `SiteManager@123` | Site operations, hazard lifecycle execution, mitigation actions |
| **Safety Officer** | `safety@acriplatform.com` | `Safety@123` | Dedicated safety intelligence, risk analysis execution, hazard closure |
| **Viewer** | `viewer@acriplatform.com` | `Viewer@123` | Read-only executive visibility. Write/analysis APIs return `403 Forbidden` |

---

## 🧮 Mathematical Risk Formula & Classification

Both frontend and backend use an identical, verified risk formula:

$$\text{Risk Score} = \left(\frac{P \times S}{25}\right) \times 100$$

Where:
- **$P$** = Probability rating (integer scale 1 to 5)
- **$S$** = Severity rating (integer scale 1 to 5)

### Verification Table & Category Thresholds:
| Multiplication ($P \times S$) | Formula Output | Risk Category |
|:-----------------------------:|:--------------:|:-------------:|
| $1 \times 1 = 1$ | **4.0** | **LOW** (0 – 24) |
| $2 \times 3 = 6$ | **24.0** | **LOW** (0 – 24) |
| $3 \times 3 = 9$ | **36.0** | **MEDIUM** (25 – 49) |
| $4 \times 4 = 16$ | **64.0** | **HIGH** (50 – 74) |
| $5 \times 5 = 25$ | **100.0** | **CRITICAL** (75 – 100) |

---

## 🔍 The 10 Deterministic Hazard Detection Rules

The `RuleBasedRiskAnalyzer` runs all site data against 10 deterministic hazard rules. Every rule specifies explicit trigger conditions, hazard type, probability, severity, evidence, and actionable recommendations:

1. **Rule 1: Excavation + Heavy Rain / Ground Saturation**
   - *Trigger:* Ongoing excavation during heavy rainfall or observed water accumulation.
   - *Hazard Type:* `HazardType.EXCAVATION` | *Score:* 100 / CRITICAL
   - *Action:* Evacuate trench, deploy dewatering pumps, require structural engineer stability inspection.
2. **Rule 2: Water Accumulation + Electrical Activity**
   - *Trigger:* Electrical work or temporary distribution panels adjacent to standing water / rain.
   - *Hazard Type:* `HazardType.ELECTRICAL` | *Score:* 80 / CRITICAL
   - *Action:* De-energize distribution boards immediately, apply Lockout/Tagout (LOTO), verify GFCI.
3. **Rule 3: Hot Work / Welding + Inadequate Fire Controls / High Heat**
   - *Trigger:* Welding/cutting active with ambient temperature > 35°C or unverified fire watch.
   - *Hazard Type:* `HazardType.FIRE` | *Score:* 64 / HIGH
   - *Action:* Mandate 30-min post-work fire watch, place dual 10kg ABC extinguishers within 10m.
4. **Rule 4: Heavy Equipment + Overdue Maintenance / Inspection**
   - *Trigger:* Active equipment with overdue inspection or maintenance status.
   - *Hazard Type:* `HazardType.EQUIPMENT` | *Score:* 48 / MEDIUM
   - *Action:* Red-tag and ground machinery until 3rd-party mechanical fitness certification is completed.
5. **Rule 5: Scaffolding + High Wind Gusts (>35 km/h)**
   - *Trigger:* Work at height on scaffolding during high wind conditions.
   - *Hazard Type:* `HazardType.FALL` | *Score:* 80 / CRITICAL
   - *Action:* Full halt of work at height; inspect base plates, ledger ties, and anchor points.
6. **Rule 6: Extreme Heat Stress (Ambient Temp ≥ 38°C)**
   - *Trigger:* High ambient temperature exceeding 38°C with active workforce.
   - *Hazard Type:* `HazardType.ENVIRONMENTAL` | *Score:* 48 / MEDIUM
   - *Action:* Enforce OSHA work-rest cycles (15m rest/45m work), provide chilled electrolytes.
7. **Rule 7: Material Handling + High Worker Density (>50 Workers)**
   - *Trigger:* Heavy overhead crane or ground transport inside congested personnel zones.
   - *Hazard Type:* `HazardType.MATERIAL_HANDLING` | *Score:* 48 / MEDIUM
   - *Action:* Erect rigid pedestrian transit corridors; assign dedicated spotters with air horns.
8. **Rule 8: Blocked Pathways & Housekeeping Deficiencies**
   - *Trigger:* Construction debris, rebar off-cuts, or blocked emergency egress corridors.
   - *Hazard Type:* `HazardType.STRUCTURAL` | *Score:* 32 / MEDIUM
   - *Action:* Site-wide 1-hour housekeeping stand-down; clear walkways to minimum 1.2m width.
9. **Rule 9: High-Risk Activities without Verified Safety Controls**
   - *Trigger:* Critical activities underway without formal Permit-to-Work or certified supervisor.
   - *Hazard Type:* `HazardType.OTHER` (Operational) | *Score:* 64 / HIGH
   - *Action:* Halt operations immediately; verify Permit-to-Work (PTW) protocols before recommencing.
10. **Rule 10: Structural Demolition Operations**
    - *Trigger:* Demolition operations with risk of uncontrolled slab failure or silica dust.
    - *Hazard Type:* `HazardType.STRUCTURAL` | *Score:* 48 / MEDIUM
    - *Action:* Enforce 1.5x height exclusion perimeter; deploy continuous dust misting cannons.

---

## 📊 Five Risk Categories

Every risk evaluation computes distinct, non-simulated scores across 5 dimensions:
1. **Environmental Risk:** Real-time weather, precipitation, ambient temperatures, and pooling water.
2. **Equipment Risk:** Machinery fleet health, overdue inspections, out-of-service units.
3. **Activity Risk:** High-risk trade composition (trenching, scaffolding, hot work, rigging).
4. **Site Condition Risk:** Physical ground stability, housekeeping, obstructions, and egress safety.
5. **Operational Risk:** Workforce density, supervisor ratio, and active hazard factors.

---

## 🔄 Hazard Lifecycle Management

Hazards progress through a strictly validated state transition pipeline:

$$\text{OPEN} \longrightarrow \text{UNDER REVIEW} \longrightarrow \text{MITIGATED} \longrightarrow \text{CLOSED}$$

- **`acknowledge`:** Transitions `OPEN` $\to$ `UNDER_REVIEW`, recording `acknowledged_at` and `acknowledged_by`.
- **`mitigate`:** Transitions to `MITIGATED`, mandating detailed `mitigation_notes` describing remediation.
- **`close`:** Permanently closes the hazard when verified safe.
- **State Hardening:** Invalid transitions (e.g. attempting to acknowledge or mitigate an already closed hazard) are rejected server-side with HTTP 400.

---

## 🦺 Milestone 2 Phase 2.1 — Safety Agent Architecture

### Engine Design
```
       SafetyAgent (Autonomous Worker Intelligence Engine)
                 ↓
       BaseSafetyAnalyzer (Extensible Abstract Interface)
                 ↓
       RuleBasedSafetyAnalyzer (Deterministic Rule Engine)
                 ↓
       Deterministic Safety Findings (Rules 1 - 6)
                 ↓
       Safety Recommendations (Actionable remediation)
                 ↓
       Database Persistence (SafetyAnalysis & SafetyFinding)
                 ↓
       Frontend UI (Site Detail, Worker Safety Profile Modal, Safety Monitoring)
```

### Deterministic Safety Rules
1. **Rule 1: PPE Violation** (`PPEStatus.NON_COMPLIANT` / `PARTIAL`) $\to$ Detects missing mandatory gear (Helmet, Safety Vest, Gloves, Safety Shoes). High/Medium severity with stop-entry recommendation.
2. **Rule 2: Expired Training** (`SafetyTrainingStatus.EXPIRED`) $\to$ Detects expired certifications, restricts assignments.
3. **Rule 3: Missing Required Training** (`NOT_STARTED` / `IN_PROGRESS` on specialized roles) $\to$ High severity with task reassignment requirement.
4. **Rule 4: Unsafe Equipment Operation** $\to$ Detects uncertified equipment operators or uninspected machinery. Generates **CRITICAL** finding with immediate lockout requirement.
5. **Rule 5: Unsafe High-Risk Activity** $\to$ Detects high-risk tasks (welding, excavation, scaffolding, demolition) performed with deficient PPE. Generates **HIGH/CRITICAL** finding.
6. **Rule 6: High-Risk Zone Exposure** $\to$ Detects workers in elevated danger zones without required safeguards. Generates **CRITICAL** finding.

### Safety Findings Lifecycle
- `OPEN` $\to$ `ACKNOWLEDGED` $\to$ `MITIGATED` $\to$ `CLOSED`
- Findings include: ID, site_id, worker_id, finding_type, description, evidence, severity (LOW, MEDIUM, HIGH, CRITICAL), recommendation, detection_source (`RULE_ENGINE`), created_at, updated_at.

### Safety Agent REST APIs
- `POST /api/v1/safety/analyze/site/{site_id}` — Autonomous site worker safety audit
- `POST /api/v1/safety/analyze/worker/{worker_id}` — Single worker safety compliance analysis
- `GET /api/v1/safety/site/{site_id}` — Site safety summary and metrics
- `GET /api/v1/safety/site/{site_id}/findings` — Site safety findings with status & severity filters
- `GET /api/v1/safety/workers/{worker_id}/findings` — Worker-specific safety history
- `GET /api/v1/safety/demo-scenarios` — List 5 deterministic safety demo scenarios
- `POST /api/v1/safety/demo-scenario` — Run deterministic safety scenario
- `PATCH /api/v1/safety/findings/{finding_id}` — Manage finding lifecycle (acknowledge, mitigate, close)

---

## 🧪 Automated Testing & Build Validation

### Running Backend Tests
```powershell
cd "Agentic AI/ACRIP/backend"
python -m pytest app/tests
```
**Results:** **105 / 105 passed** (100% test pass rate across Milestone 1, Phase 2.1, Phase 2.2, and Phase 2.3).
- `test_phase1_2.py`: 22 / 22 passed
- `test_phase1_3.py`: 20 / 20 passed
- `test_phase2_1.py`: 17 / 17 passed
- `test_phase2_2.py`: 23 / 23 passed
- `test_phase2_3.py`: 23 / 23 passed

### Running Frontend Validation
```powershell
cd "Agentic AI/ACRIP/frontend"
npm run build
```
**Results:** **0 TypeScript errors, 0 build errors**. Production bundle compiled successfully (Vite v5.4.21 in 7.86s).

---

## 🏆 Exact Hackathon Demo Walkthrough Sequence

Follow these exact steps for the live demonstration:

1. **Login:**
   - Navigate to `http://localhost:5173`.
   - Log in using `safety@acriplatform.com` / `Safety@123` (Safety Officer).
2. **Executive Dashboard:**
   - Review overall platform metrics, active hazards count, and site status overview cards.
3. **Open Project & Site:**
   - Click **Projects** in the navigation, select **Skyline Tower Construction (PRJ-001)**.
   - Click on site **Skyline Tower — Hyderabad Central (SITE-001)**.
4. **Trigger Autonomous Risk Analysis:**
   - View the site details header and gauge.
   - Click the prominent **`ANALYZE SITE RISK`** button.
   - Observe the real-time evaluation loading state.
   - Review the generated modal showing detected hazards, exact probability/severity factors, score (e.g., 93.7/100 CRITICAL), and actionable mitigation recommendations.
5. **Inspect Risk Monitoring Dashboard:**
   - Navigate to **Risk Monitoring** in the sidebar.
   - View the **Overall Site Risk** gauge and status badge.
   - Inspect the **5 Risk Category Cards** (Environmental, Equipment, Activity, Site Condition, Operational).
   - View the **Site Risk Score Trend Chart** populated with real historical records.
6. **Execute Deterministic Demo Scenarios:**
   - In the Demo Scenarios bar, click **Scenario 4 (Trench Flood)** $\to$ Watch the risk escalate to **CRITICAL**.
   - Click **Scenario 1 (Baseline)** $\to$ Watch the score reset to **LOW**.
7. **Manage Hazard Lifecycle:**
   - In the **Hazard Detection & Observation Table**, click on an open hazard row.
   - The `HazardDetailModal` opens displaying the detection evidence and rule engine source.
   - Click **Acknowledge (Review)** $\to$ Hazard updates to **Under Review**.
   - Click **Record Mitigation Action**, enter notes (e.g., *"Deployed submersible pumps and trench shoring"*), and click **Confirm Mitigation** $\to$ Hazard updates to **Mitigated**.
   - Click **Close Hazard** $\to$ Hazard marks as **Closed**.
8. **Verify Real-Time Notifications:**
   - Open the notification bell in the top navigation bar.
   - Notice high and critical hazard alerts generated by the agent with deduplication active.
