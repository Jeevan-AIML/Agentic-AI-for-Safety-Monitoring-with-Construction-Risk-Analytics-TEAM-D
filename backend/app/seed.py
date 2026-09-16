"""
ACRIP Seed Data
===============
Realistic demo data for development and demonstration.
IMPORTANT: This is mock/demo data only. In production, real data
comes from site operations and (Phase 1.2+) the Site Risk Agent.

To run: python -m app.seed
"""

import uuid
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.database.session import SessionLocal, engine
from app.models.models import (
    Base, User, Project, Site, Worker, Equipment, Activity,
    Hazard, RiskScore, Inspection, Notification,
    UserRole, ProjectStatus, SiteStatus, WorkerRole,
    SafetyTrainingStatus, PPEStatus, EquipmentStatus,
    ActivityType, HazardType, HazardStatus, RiskCategory,
    NotificationCategory
)
from app.core.security import hash_password
from app.core.config import settings
from app.services.risk_scoring import calculate_risk_score, get_risk_category

# Create all tables
Base.metadata.create_all(bind=engine)


def seed_database():
    db: Session = SessionLocal()
    try:
        # Skip if already seeded
        if db.query(User).filter(User.email == "admin@acriplatform.com").first():
            print("[INFO] Database already seeded. Skipping.")
            return

        print("[INFO] Seeding ACRIP database...")

        # ── Users ─────────────────────────────────────────────────────────

        admin = User(
            id=str(uuid.uuid4()), email="admin@acriplatform.com",
            full_name="Alex Morgan", hashed_password=hash_password(settings.DEMO_ADMIN_PASSWORD),
            role=UserRole.SUPER_ADMIN, is_active=True, is_verified=True,
            department="Administration", phone="+91-9000000001",
        )
        manager = User(
            id=str(uuid.uuid4()), email="manager@acriplatform.com",
            full_name="Priya Sharma", hashed_password=hash_password(settings.DEMO_MANAGER_PASSWORD),
            role=UserRole.PROJECT_MANAGER, is_active=True, is_verified=True,
            department="Project Management", phone="+91-9000000002",
        )
        site_mgr = User(
            id=str(uuid.uuid4()), email="site.manager@acriplatform.com",
            full_name="Rajesh Kumar", hashed_password=hash_password(settings.DEMO_SITE_MANAGER_PASSWORD),
            role=UserRole.SITE_MANAGER, is_active=True, is_verified=True,
            department="Site Operations", phone="+91-9000000003",
        )
        safety_off = User(
            id=str(uuid.uuid4()), email="safety@acriplatform.com",
            full_name="Anita Patel", hashed_password=hash_password(settings.DEMO_SAFETY_PASSWORD),
            role=UserRole.SAFETY_OFFICER, is_active=True, is_verified=True,
            department="Safety & Compliance", phone="+91-9000000004",
        )
        viewer = User(
            id=str(uuid.uuid4()), email="viewer@acriplatform.com",
            full_name="Suresh Reddy", hashed_password=hash_password(settings.DEMO_VIEWER_PASSWORD),
            role=UserRole.VIEWER, is_active=True, is_verified=True,
            department="Executive", phone="+91-9000000005",
        )

        for u in [admin, manager, site_mgr, safety_off, viewer]:
            db.add(u)
        db.flush()

        # ── Projects ───────────────────────────────────────────────────────

        skyline_project = Project(
            id=str(uuid.uuid4()), project_id="PRJ-001",
            name="Skyline Tower Construction",
            client="Skyline Developers Pvt. Ltd.",
            description="50-storey commercial tower construction in Hyderabad city center. Premium Grade-A office space with underground parking.",
            start_date=datetime(2025, 1, 15),
            expected_completion=datetime(2027, 6, 30),
            budget=850000000.0,
            status=ProjectStatus.ACTIVE,
            manager_id=manager.id,
            address="Plot No. 42, Hitech City",
            city="Hyderabad", state="Telangana", country="India",
            latitude=17.4435, longitude=78.3772,
        )
        metro_project = Project(
            id=str(uuid.uuid4()), project_id="PRJ-002",
            name="Metro Rail Extension — Phase 3",
            client="Hyderabad Metro Rail Ltd.",
            description="12km extension of Hyderabad Metro Rail covering 8 new stations.",
            start_date=datetime(2025, 6, 1),
            expected_completion=datetime(2027, 12, 31),
            budget=3200000000.0,
            status=ProjectStatus.ACTIVE,
            manager_id=manager.id,
            address="GHMC Road, Miyapur",
            city="Hyderabad", state="Telangana", country="India",
            latitude=17.4949, longitude=78.3432,
        )
        bridge_project = Project(
            id=str(uuid.uuid4()), project_id="PRJ-003",
            name="Outer Ring Road Bridge Upgrade",
            client="NHAI — National Highways Authority",
            description="Structural reinforcement and widening of 6 bridges on the Outer Ring Road.",
            start_date=datetime(2025, 3, 1),
            expected_completion=datetime(2026, 9, 30),
            budget=420000000.0,
            status=ProjectStatus.ACTIVE,
            manager_id=manager.id,
            city="Hyderabad", state="Telangana", country="India",
        )
        planning_project = Project(
            id=str(uuid.uuid4()), project_id="PRJ-004",
            name="Residential Complex — Green Valley",
            client="Green Valley Homes",
            description="320-unit residential complex with amenities.",
            start_date=datetime(2026, 3, 1),
            expected_completion=datetime(2028, 6, 30),
            budget=550000000.0,
            status=ProjectStatus.PLANNING,
            manager_id=manager.id,
            city="Pune", state="Maharashtra", country="India",
        )

        for p in [skyline_project, metro_project, bridge_project, planning_project]:
            db.add(p)
        db.flush()

        # ── Sites ──────────────────────────────────────────────────────────

        skyline_site = Site(
            id=str(uuid.uuid4()), site_id="SITE-001",
            name="Skyline Tower — Hyderabad Central",
            site_type="High-Rise Construction",
            project_id=skyline_project.id,
            manager_id=site_mgr.id,
            status=SiteStatus.WARNING,
            current_risk_score=72.0,
            risk_category=RiskCategory.HIGH,
            address="Plot 42, Hitech City, Madhapur",
            city="Hyderabad", state="Telangana", country="India",
            latitude=17.4435, longitude=78.3772,
            worker_count=120, equipment_count=18,
            last_inspection=datetime.utcnow() - timedelta(days=5),
        )
        metro_site_a = Site(
            id=str(uuid.uuid4()), site_id="SITE-002",
            name="Metro Extension — Miyapur Station",
            site_type="Underground Construction",
            project_id=metro_project.id,
            status=SiteStatus.ACTIVE,
            current_risk_score=48.0,
            risk_category=RiskCategory.MEDIUM,
            city="Hyderabad", state="Telangana", country="India",
            latitude=17.4949, longitude=78.3432,
            worker_count=85, equipment_count=12,
            last_inspection=datetime.utcnow() - timedelta(days=2),
        )
        metro_site_b = Site(
            id=str(uuid.uuid4()), site_id="SITE-003",
            name="Metro Extension — Chandanagar Depot",
            site_type="Rail Infrastructure",
            project_id=metro_project.id,
            status=SiteStatus.MONITORING,
            current_risk_score=35.0,
            risk_category=RiskCategory.MEDIUM,
            city="Hyderabad", state="Telangana", country="India",
            latitude=17.4868, longitude=78.3144,
            worker_count=60, equipment_count=9,
            last_inspection=datetime.utcnow() - timedelta(days=8),
        )
        bridge_site = Site(
            id=str(uuid.uuid4()), site_id="SITE-004",
            name="ORR Bridge — Kompally Section",
            site_type="Bridge Construction",
            project_id=bridge_project.id,
            status=SiteStatus.CRITICAL,
            current_risk_score=81.0,
            risk_category=RiskCategory.CRITICAL,
            city="Hyderabad", state="Telangana", country="India",
            latitude=17.5434, longitude=78.4897,
            worker_count=45, equipment_count=8,
            last_inspection=datetime.utcnow() - timedelta(days=12),
        )

        # Assign site manager to skyline site
        site_mgr.assigned_site_id = skyline_site.id

        for s in [skyline_site, metro_site_a, metro_site_b, bridge_site]:
            db.add(s)
        db.flush()

        # ── Workers ────────────────────────────────────────────────────────

        worker_names = [
            ("Mohammad Irfan", WorkerRole.OPERATOR),
            ("Venkat Rao", WorkerRole.MASON),
            ("Sanjay Gupta", WorkerRole.ELECTRICIAN),
            ("Ramesh Naidu", WorkerRole.SUPERVISOR),
            ("Arun Kumar", WorkerRole.WELDER),
            ("Deepak Singh", WorkerRole.TECHNICIAN),
            ("Suresh Babu", WorkerRole.GENERAL_WORKER),
            ("Ravi Prasad", WorkerRole.MASON),
            ("Kiran Kumar", WorkerRole.OPERATOR),
            ("Srinivas Reddy", WorkerRole.SUPERVISOR),
            ("Naresh Yadav", WorkerRole.WELDER),
            ("Bhaskar Rao", WorkerRole.ELECTRICIAN),
            ("Mahesh Patil", WorkerRole.GENERAL_WORKER),
            ("Raju Sharma", WorkerRole.MASON),
            ("Ajay Verma", WorkerRole.TECHNICIAN),
        ]
        training_choices = list(SafetyTrainingStatus)
        ppe_choices = list(PPEStatus)
        workers = []
        for i, (name, role) in enumerate(worker_names, 1):
            w = Worker(
                id=str(uuid.uuid4()),
                worker_id=f"WRK-{i:04d}",
                name=name,
                role=role,
                department=random.choice(["Civil", "Mechanical", "Electrical", "Safety"]),
                site_id=skyline_site.id,
                contact=f"+91-90{random.randint(10000000, 99999999)}",
                joining_date=datetime(2025, 1, 15) + timedelta(days=random.randint(0, 100)),
                safety_training=random.choice(training_choices),
                ppe_status=random.choice(ppe_choices),
            )
            workers.append(w)
            db.add(w)

        db.flush()

        # ── Equipment ──────────────────────────────────────────────────────

        equipment_list = [
            ("Tower Crane TC-01", "Crane", "Liebherr", "LTM 1300-6.2"),
            ("Excavator EX-01", "Excavator", "Caterpillar", "CAT 390F"),
            ("Concrete Pump CP-01", "Concrete Pump", "Schwing", "S 52 SX"),
            ("Forklift FL-01", "Forklift", "Toyota", "8FGCU25"),
            ("Scaffolding Set A", "Scaffolding", "Layher", "Allround"),
            ("Generator GEN-01", "Generator", "Cummins", "C500D5"),
            ("Concrete Mixer CM-01", "Concrete Mixer", "Schwing", "Stetter M5"),
            ("Welding Machine WM-01", "Welding Machine", "Lincoln Electric", "Power Wave"),
            ("Aerial Work Platform AWP-01", "AWP", "JLG", "800AJ"),
            ("Mobile Crane MC-01", "Crane", "Tadano", "GR-800EX"),
            ("Compactor CP-02", "Compactor", "Dynapac", "CA2500D"),
            ("Pile Driver PD-01", "Pile Driver", "Junttan", "PM25"),
        ]
        eq_status = list(EquipmentStatus)
        for i, (name, etype, mfr, model) in enumerate(equipment_list, 1):
            e = Equipment(
                id=str(uuid.uuid4()),
                equipment_id=f"EQP-{i:04d}",
                name=name,
                equipment_type=etype,
                manufacturer=mfr,
                model=model,
                site_id=skyline_site.id,
                operator_name=random.choice([w.name for w in workers[:5]]),
                status=random.choice([EquipmentStatus.OPERATIONAL, EquipmentStatus.OPERATIONAL, EquipmentStatus.INSPECTION_DUE]),
                last_inspection=datetime.utcnow() - timedelta(days=random.randint(5, 45)),
                maintenance_due=datetime.utcnow() + timedelta(days=random.randint(5, 90)),
            )
            db.add(e)
        db.flush()

        # ── Activities ─────────────────────────────────────────────────────

        activity_data = [
            (ActivityType.EXCAVATION, "Deep foundation excavation for Tower Block A", 25),
            (ActivityType.CONCRETE_WORK, "Basement slab concrete pouring — Level B2", 40),
            (ActivityType.WELDING, "Structural steel welding — Floor 12", 8),
            (ActivityType.SCAFFOLDING, "Scaffolding erection — East facade", 15),
            (ActivityType.ELECTRICAL_WORK, "Main electrical conduit installation — Floors 5-8", 12),
            (ActivityType.MATERIAL_HANDLING, "Steel beam delivery and placement", 20),
            (ActivityType.GENERAL_CONSTRUCTION, "Brickwork — Level 3 internal walls", 18),
            (ActivityType.CONCRETE_WORK, "Column concrete — Floor 14", 30),
        ]
        for i, (atype, desc, workers_n) in enumerate(activity_data):
            a = Activity(
                id=str(uuid.uuid4()),
                site_id=skyline_site.id,
                activity_type=atype,
                description=desc,
                date=datetime.utcnow() - timedelta(days=i),
                start_time="07:00",
                end_time="17:00",
                workers_involved=workers_n,
                environmental_conditions=random.choice(["Clear", "Partly Cloudy", "Windy", "Overcast"]),
                notes="Normal operations. Safety briefing conducted.",
                created_by=site_mgr.id,
            )
            db.add(a)
        db.flush()

        # ── Hazards ────────────────────────────────────────────────────────

        hazard_data = [
            (HazardType.FALL, "Inadequate edge protection on Floor 14", 5, 4, "Install guardrails immediately. Restrict access until secured."),
            (HazardType.EQUIPMENT, "Tower crane TC-01 shows abnormal vibration", 4, 4, "Stop crane operations. Conduct immediate mechanical inspection."),
            (HazardType.STRUCTURAL, "Temporary formwork showing signs of deflection", 4, 3, "Reinforce formwork supports. Consult structural engineer."),
            (HazardType.ELECTRICAL, "Exposed wiring near water accumulation area", 3, 4, "Isolate circuit. Waterproof wiring immediately."),
            (HazardType.ENVIRONMENTAL, "Dust levels exceed safety limits — north sector", 3, 3, "Deploy dust suppression systems. Mandate respiratory PPE."),
            (HazardType.FIRE, "Welding operations near flammable materials", 4, 2, "Establish fire exclusion zones. Station fire watch."),
            (HazardType.EXCAVATION, "Trench walls showing signs of instability", 5, 3, "Shore trench walls. Evacuate workers from area."),
            (HazardType.MATERIAL_HANDLING, "Overloaded material hoist — exceeds rated capacity", 3, 2, "Reduce load. Re-train operators on capacity limits."),
        ]
        hazard_statuses = [HazardStatus.OPEN, HazardStatus.OPEN, HazardStatus.UNDER_REVIEW,
                           HazardStatus.OPEN, HazardStatus.MITIGATED, HazardStatus.OPEN,
                           HazardStatus.UNDER_REVIEW, HazardStatus.CLOSED]

        for i, (htype, desc, sev, prob, action) in enumerate(hazard_data):
            risk = calculate_risk_score(prob, sev)
            cat = get_risk_category(risk)
            h = Hazard(
                id=str(uuid.uuid4()),
                hazard_id=f"HAZ-{i+1:04d}",
                site_id=skyline_site.id,
                hazard_type=htype,
                description=desc,
                severity=sev,
                probability=prob,
                risk_score=risk,
                risk_category=cat,
                status=hazard_statuses[i],
                detected_at=datetime.utcnow() - timedelta(hours=random.randint(2, 72)),
                reported_by="Anita Patel" if i % 2 == 0 else "Rajesh Kumar",
                recommended_action=action,
                detected_by_agent=False,
            )
            db.add(h)

        # Also add hazards to other sites
        db.add(Hazard(
            id=str(uuid.uuid4()), hazard_id="HAZ-0009",
            site_id=bridge_site.id,
            hazard_type=HazardType.STRUCTURAL,
            description="Concrete spalling detected on bridge deck — Section 4",
            severity=5, probability=4,
            risk_score=calculate_risk_score(4, 5),
            risk_category=RiskCategory.CRITICAL,
            status=HazardStatus.OPEN,
            detected_at=datetime.utcnow() - timedelta(hours=24),
            reported_by="Site Inspector",
            recommended_action="Immediate structural assessment required. Cordon off area.",
            detected_by_agent=False,
        ))
        db.flush()

        # ── Risk Scores ────────────────────────────────────────────────────

        # Historical risk scores for Skyline site (30-day history)
        for days_ago in range(30, 0, -1):
            base = 72 + random.uniform(-8, 8)
            env = 68 + random.uniform(-5, 5)
            eq = 54 + random.uniform(-5, 5)
            sc = 82 + random.uniform(-4, 4)
            op = 61 + random.uniform(-4, 4)
            rs = RiskScore(
                id=str(uuid.uuid4()),
                site_id=skyline_site.id,
                overall_score=round(base, 1),
                category=get_risk_category(base),
                environmental_risk=round(env, 1),
                equipment_risk=round(eq, 1),
                site_condition_risk=round(sc, 1),
                operational_risk=round(op, 1),
                calculated_by="manual",  # Phase 1.2: will be "site_risk_agent"
                recorded_at=datetime.utcnow() - timedelta(days=days_ago),
            )
            db.add(rs)

        # Current risk scores for other sites
        for site, env, eq, sc, op in [
            (metro_site_a, 45, 38, 52, 41),
            (metro_site_b, 30, 28, 40, 35),
            (bridge_site, 75, 80, 85, 78),
        ]:
            overall = round(env * 0.25 + eq * 0.30 + sc * 0.25 + op * 0.20, 1)
            db.add(RiskScore(
                id=str(uuid.uuid4()),
                site_id=site.id,
                overall_score=overall,
                category=get_risk_category(overall),
                environmental_risk=float(env),
                equipment_risk=float(eq),
                site_condition_risk=float(sc),
                operational_risk=float(op),
                calculated_by="manual",
            ))
        db.flush()

        # ── Inspections ────────────────────────────────────────────────────

        for i, (site, result, findings) in enumerate([
            (skyline_site, "Conditional", "Edge protection inadequate on upper floors. Electrical conduits not properly sealed."),
            (skyline_site, "Pass", "General safety measures in place. Minor housekeeping improvements required."),
            (metro_site_a, "Pass", "Safety nets and barriers correctly installed. PPE compliance at 94%."),
            (bridge_site, "Fail", "Concrete deterioration detected. Structural integrity assessment required immediately."),
        ]):
            insp = Inspection(
                id=str(uuid.uuid4()),
                inspection_id=f"INSP-{i+1:04d}",
                site_id=site.id,
                inspector_name="Anita Patel",
                date=datetime.utcnow() - timedelta(days=i * 5 + 2),
                result=result,
                findings=findings,
                notes="Inspection conducted per OSHA and IS standards.",
            )
            db.add(insp)
        db.flush()

        # ── Notifications ──────────────────────────────────────────────────

        notif_data = [
            (NotificationCategory.RISK, "High-risk hazard detected at Skyline Tower",
             "Fall hazard (CRITICAL) detected on Floor 14. Immediate action required.", "critical",
             "/sites/SITE-001"),
            (NotificationCategory.SAFETY, "Equipment inspection overdue - EQP-0004",
             "Forklift FL-01 is overdue for scheduled inspection. Operations suspended.", "warning",
             "/equipment"),
            (NotificationCategory.RISK, "Site risk score increased to 72",
             "Skyline Tower risk score elevated to HIGH (72/100). Review site conditions.", "warning",
             "/risk-monitoring"),
            (NotificationCategory.COMPLIANCE, "Excavation inspection scheduled",
             "Foundation excavation requires mandatory inspection by tomorrow (14 Sep).", "info",
             "/sites/SITE-001"),
            (NotificationCategory.SAFETY, "PPE compliance drop - Site 001",
             "PPE compliance at Skyline Tower dropped to 78%. Immediate intervention needed.", "warning",
             "/sites/SITE-001"),
            (NotificationCategory.RISK, "CRITICAL risk at ORR Bridge site",
             "Structural hazard classified CRITICAL (81/100) at Kompally Bridge section.", "critical",
             "/sites/SITE-004"),
            (NotificationCategory.SYSTEM, "AI Monitoring System online",
             "ACRIP monitoring system initialized. Site Risk Agent integration pending (Phase 1.2).", "info",
             "/dashboard"),
            (NotificationCategory.COMPLIANCE, "Monthly safety report due",
             "September safety compliance report is due by Sep 30, 2026.", "info",
             "/reports"),
        ]

        for category, title, message, severity, link in notif_data:
            db.add(Notification(
                id=str(uuid.uuid4()),
                user_id=None,  # Broadcast to all users
                category=category,
                title=title,
                message=message,
                severity=severity,
                link=link,
                is_read=False,
            ))

        db.commit()
        print("[SUCCESS] Database seeded successfully!")
        print("\n[INFO] Demo Credentials:")
        print("  Super Admin    : admin@acriplatform.com       / Admin@123")
        print("  Project Manager: manager@acriplatform.com     / Manager@123")
        print("  Site Manager   : site.manager@acriplatform.com / SiteManager@123")
        print("  Safety Officer : safety@acriplatform.com       / Safety@123")
        print("  Viewer         : viewer@acriplatform.com        / Viewer@123")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
