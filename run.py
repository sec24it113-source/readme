import os
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import click
from app import create_app
from app.extensions import db
from app.models import (
    User, UserRole, Event, EventStatus, TicketType, TicketInventory,
    get_utc_now
)

app = create_app(os.getenv("FLASK_ENV", "development"))
celery = app.extensions.get("celery")


@app.cli.command("init-db")
def init_db():
    """Create all database tables."""
    with app.app_context():
        db.create_all()
        click.echo("Database tables created successfully.")


@app.cli.command("create-admin")
@click.option("--email", default="admin@eventhub.com", help="Admin email address")
@click.option("--password", default="AdminPass123!", help="Admin secure password")
@click.option("--name", default="Platform Administrator", help="Admin full name")
def create_admin(email, password, name):
    """Safe development CLI command to initialize or update the platform administrator."""
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(email=email.strip().lower()).first()
        if user:
            user.role = UserRole.ADMIN
            user.full_name = name
            user.set_password(password)
            click.echo(f"Admin user '{email}' updated successfully.")
        else:
            user = User(
                email=email.strip().lower(),
                full_name=name,
                role=UserRole.ADMIN,
                is_active=True
            )
            user.set_password(password)
            db.session.add(user)
            click.echo(f"Admin user '{email}' created successfully.")
        db.session.commit()


@app.cli.command("seed-data")
def seed_data():
    """Seed demo organizers, events, ticket tiers, and attendees."""
    with app.app_context():
        db.create_all()

        # 1. Admin
        admin = User.query.filter_by(email="admin@eventhub.com").first()
        if not admin:
            admin = User(
                email="admin@eventhub.com",
                full_name="Platform Admin",
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password("AdminPass123!")
            db.session.add(admin)

        # 2. Organizer 1
        org1 = User.query.filter_by(email="organizer@techconf.org").first()
        if not org1:
            org1 = User(
                email="organizer@techconf.org",
                full_name="Tech Global Summits",
                role=UserRole.ORGANIZER,
                is_active=True
            )
            org1.set_password("OrganizerPass123!")
            db.session.add(org1)

        # 3. Organizer 2
        org2 = User.query.filter_by(email="organizer@musicfest.com").first()
        if not org2:
            org2 = User(
                email="organizer@musicfest.com",
                full_name="SoundWave Productions",
                role=UserRole.ORGANIZER,
                is_active=True
            )
            org2.set_password("OrganizerPass123!")
            db.session.add(org2)

        # 4. Attendee
        attendee = User.query.filter_by(email="attendee@example.com").first()
        if not attendee:
            attendee = User(
                email="attendee@example.com",
                full_name="Jane Doe",
                role=UserRole.ATTENDEE,
                is_active=True
            )
            attendee.set_password("AttendeePass123!")
            db.session.add(attendee)

        db.session.commit()

        # 5. Events
        now = get_utc_now()
        event1 = Event.query.filter_by(title="Global Cloud & AI Summit 2026").first()
        if not event1:
            future_date = (now + timedelta(days=45)).date()
            sales_cutoff = now + timedelta(days=44)
            event1 = Event(
                organizer_id=org1.id,
                title="Global Cloud & AI Summit 2026",
                description="Join over 5,000 developers, architects, and technology leaders for 3 days of deep-dive workshops, keynote sessions, and networking.",
                category="Technology",
                venue="Metropolitan Convention Center, Hall A",
                event_date=future_date,
                start_time=time(9, 0),
                end_time=time(18, 0),
                sales_cutoff=sales_cutoff,
                status=EventStatus.PUBLISHED,
                image_url="https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop"
            )
            db.session.add(event1)
            db.session.flush()

            # Add Ticket Tiers
            tiers = [
                ("General Admission", "Full access to all keynote sessions and expo floor", Decimal("199.00"), 250),
                ("VIP All-Access", "Includes VIP lounge, speaker dinner, and priority seating", Decimal("499.00"), 50),
                ("Student Pass", "Valid student ID required at badge pickup", Decimal("79.00"), 100),
            ]
            for name, desc, price, qty in tiers:
                tt = TicketType(event_id=event1.id, name=name, description=desc, price=price)
                db.session.add(tt)
                db.session.flush()
                inv = TicketInventory(ticket_type_id=tt.id, total_quantity=qty, available_quantity=qty, held_quantity=0, sold_quantity=0)
                db.session.add(inv)

        event2 = Event.query.filter_by(title="Summer Neon Music Festival").first()
        if not event2:
            future_date = (now + timedelta(days=60)).date()
            sales_cutoff = now + timedelta(days=59)
            event2 = Event(
                organizer_id=org2.id,
                title="Summer Neon Music Festival",
                description="Experience world-class electronic music, immersive laser visuals, and food trucks under the stars.",
                category="Music",
                venue="Riverside Amphitheater Park",
                event_date=future_date,
                start_time=time(16, 0),
                end_time=time(23, 30),
                sales_cutoff=sales_cutoff,
                status=EventStatus.PUBLISHED,
                image_url="https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800&auto=format&fit=crop"
            )
            db.session.add(event2)
            db.session.flush()

            music_tiers = [
                ("Standard Lawn Pass", "General admission open lawn seating", Decimal("85.00"), 500),
                ("Golden Circle Pit", "Standing room right in front of main stage", Decimal("175.00"), 150),
            ]
            for name, desc, price, qty in music_tiers:
                tt = TicketType(event_id=event2.id, name=name, description=desc, price=price)
                db.session.add(tt)
                db.session.flush()
                inv = TicketInventory(ticket_type_id=tt.id, total_quantity=qty, available_quantity=qty, held_quantity=0, sold_quantity=0)
                db.session.add(inv)

        db.session.commit()
        click.echo("Sample database records seeded successfully.")


if __name__ == "__main__":
    from app.tasks.cleanup import start_background_scheduler
    start_background_scheduler(app, interval_seconds=30)
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
