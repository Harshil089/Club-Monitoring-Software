import pytest
from django.urls import reverse
from core.models import Club, Semester, Event, Ranking
from core.services import calculate_club_performance

@pytest.mark.django_db
def test_cps_calculation_and_ranking():
    # Setup
    semester = Semester.objects.create(name="Fall 2023", is_active=True)
    club_a = Club.objects.create(name="Coding Club", short_code="CODE", faculty_incharge="Dr. A", student_lead="Alice")
    club_b = Club.objects.create(name="Robotics Club", short_code="BOT", faculty_incharge="Dr. B", student_lead="Bob")
    club_c = Club.objects.create(name="Music Club", short_code="MUSIC", faculty_incharge="Dr. C", student_lead="Charlie")

    # Event 1 for Club A (Perfect scores) -> Total 100
    Event.objects.create(
        club=club_a, semester=semester, name="Hackathon", date="2023-09-01",
        expected_turnout=100, actual_turnout=100,
        planning_score=20, execution_score=20, documentation_score=20, innovation_score=20, turnout_score=20
    )

    # Check intermediate state: 1 event < 2 required. Tier should be Pending.
    ranking_a = Ranking.objects.get(club=club_a, semester=semester)
    assert ranking_a.cps == 100.0
    assert ranking_a.tier == 'P'
    assert ranking_a.event_count == 1

    # Event 2 for Club A (Average scores) -> Total 80
    Event.objects.create(
        club=club_a, semester=semester, name="Workshop", date="2023-09-15",
        expected_turnout=50, actual_turnout=50,
        planning_score=16, execution_score=16, documentation_score=16, innovation_score=16, turnout_score=16
    )

    # Now Club A has 2 events. Avg Score = (100 + 80) / 2 = 90.
    # Actually, logic is avg of metrics.
    # Event 1 metrics: all 20.
    # Event 2 metrics: all 16.
    # Avg Planning = (20+16)/2 = 18.
    # CPS = 18+18+18+18+18 = 90.
    # Tier should be A (>=90).
    ranking_a.refresh_from_db()
    assert ranking_a.cps == 90.0
    assert ranking_a.tier == 'A'
    assert ranking_a.event_count == 2
    assert ranking_a.rank == 1

    # Club B: 2 Events, Score 70 each -> CPS 70. Tier C (60-74).
    Event.objects.create(
        club=club_b, semester=semester, name="Bot War", date="2023-10-01",
        expected_turnout=50, actual_turnout=40,
        planning_score=14, execution_score=14, documentation_score=14, innovation_score=14, turnout_score=14
    )
    Event.objects.create(
        club=club_b, semester=semester, name="Expo", date="2023-10-02",
        expected_turnout=50, actual_turnout=40,
        planning_score=14, execution_score=14, documentation_score=14, innovation_score=14, turnout_score=14
    )

    ranking_b = Ranking.objects.get(club=club_b, semester=semester)
    assert ranking_b.cps == 70.0
    assert ranking_b.tier == 'C'

    # Club C: 2 Events, Score 50 each -> CPS 50. Tier D (<60).
    Event.objects.create(
        club=club_c, semester=semester, name="Jam", date="2023-10-01",
        expected_turnout=50, actual_turnout=40,
        planning_score=10, execution_score=10, documentation_score=10, innovation_score=10, turnout_score=10
    )
    Event.objects.create(
        club=club_c, semester=semester, name="Concert", date="2023-10-02",
        expected_turnout=50, actual_turnout=40,
        planning_score=10, execution_score=10, documentation_score=10, innovation_score=10, turnout_score=10
    )

    ranking_c = Ranking.objects.get(club=club_c, semester=semester)
    assert ranking_c.cps == 50.0
    assert ranking_c.tier == 'D'

    # Check Ranks
    # A (90) -> Rank 1
    # B (70) -> Rank 2
    # C (50) -> Rank 3
    ranking_a.refresh_from_db()
    ranking_b.refresh_from_db()
    ranking_c.refresh_from_db()

    assert ranking_a.rank == 1
    assert ranking_b.rank == 2
    assert ranking_c.rank == 3

    # Test Recalculation on Update
    # Update Club B's event to have perfect scores.
    event_b = Event.objects.filter(club=club_b).first()
    event_b.planning_score = 20
    event_b.execution_score = 20
    event_b.documentation_score = 20
    event_b.innovation_score = 20
    event_b.turnout_score = 20
    event_b.save()

    # New Avg for B:
    # Event 1: 20s. Event 2: 14s.
    # Avg: 17. CPS = 17*5 = 85.
    # Tier B (75-89).
    ranking_b.refresh_from_db()
    assert ranking_b.cps == 85.0
    assert ranking_b.tier == 'B'

    # Ranks remain 1, 2, 3 since 90 > 85 > 50.

    # Test Recalculation on Delete
    # Delete Club A's events.
    Event.objects.filter(club=club_a).delete()

    # Ranking should be gone or reset? Service says .delete() if 0 events.
    assert not Ranking.objects.filter(club=club_a, semester=semester).exists()

    # Now B should be Rank 1, C Rank 2.
    ranking_b.refresh_from_db()
    ranking_c.refresh_from_db()

    assert ranking_b.rank == 1
    assert ranking_c.rank == 2

@pytest.mark.django_db
def test_views(client):
    user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
    client.force_login(user)

    semester = Semester.objects.create(name="Fall 2023", is_active=True)
    response = client.get(reverse('dashboard'))
    assert response.status_code == 200

    club = Club.objects.create(name="Test Club", short_code="TEST", faculty_incharge="F", student_lead="S")
    response = client.get(reverse('club_detail', args=[club.id]))
    assert response.status_code == 200

from django.contrib.auth.models import User
