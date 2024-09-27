import courses.models as db
from datetime import datetime, timedelta
from typing import Optional


def create_offering(offering_name: str="ece496 fall 2024", course_name: str="ece496") -> db.Offering:
    intitution = db.Institution.objects.create()
    course = db.Course.objects.create(
        institution=intitution,
        name=course_name,
        slug="test",
        
    )
    offering = db.Offering.objects.create(
        name=offering_name,
        course=course,
        start=datetime.now(),
        end=datetime.now() + timedelta(days=100),
        active=True
    )

    return offering