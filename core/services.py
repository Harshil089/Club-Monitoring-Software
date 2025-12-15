from django.db.models import Avg, Count
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import Event, Ranking, Club, Semester, AuditLog
from .middleware import get_current_user

def create_audit_log(instance, action, details):
    user = get_current_user()
    # If called from shell/test where no middleware, user might be None
    # Just try to handle it gracefully
    if user and not user.is_authenticated:
        user = None

    AuditLog.objects.create(
        user=user,
        action=action,
        details=details
    )

def calculate_club_performance(club, semester):
    """
    Calculates CPS and assigns Tier for a club in a given semester.
    Updates or creates the Ranking object.
    """
    events = Event.objects.filter(club=club, semester=semester)
    event_count = events.count()

    if event_count == 0:
        # Reset ranking if no events
        Ranking.objects.filter(club=club, semester=semester).delete()
        return

    averages = events.aggregate(
        avg_planning=Avg('planning_score'),
        avg_execution=Avg('execution_score'),
        avg_documentation=Avg('documentation_score'),
        avg_innovation=Avg('innovation_score'),
        avg_turnout=Avg('turnout_score')
    )

    avg_planning = averages['avg_planning'] or 0
    avg_execution = averages['avg_execution'] or 0
    avg_documentation = averages['avg_documentation'] or 0
    avg_innovation = averages['avg_innovation'] or 0
    avg_turnout = averages['avg_turnout'] or 0

    cps = avg_planning + avg_execution + avg_documentation + avg_innovation + avg_turnout

    # Tier Assignment
    # FR-12: Minimum 2 events
    if event_count < 2:
        tier = 'P' # Pending
    else:
        if cps >= 90:
            tier = 'A'
        elif cps >= 75:
            tier = 'B'
        elif cps >= 60:
            tier = 'C'
        else:
            tier = 'D'

    ranking, created = Ranking.objects.update_or_create(
        club=club,
        semester=semester,
        defaults={
            'cps': cps,
            'tier': tier,
            'event_count': event_count,
            'avg_planning': avg_planning,
            'avg_execution': avg_execution,
            'avg_documentation': avg_documentation,
            'avg_innovation': avg_innovation,
            'avg_turnout': avg_turnout,
        }
    )

    # Audit Log for Calculation
    action = "Semester Calculation"
    details = f"Recalculated for {club.short_code} in {semester}. CPS: {cps}, Tier: {tier}"
    create_audit_log(ranking, action, details)

    return ranking

def update_semester_ranks(semester):
    """
    Updates the 'rank' field for all clubs in the semester based on CPS.
    """
    # Added secondary sort by club name for deterministic ordering
    rankings = Ranking.objects.filter(semester=semester).order_by('-cps', 'club__name')
    current_rank = 1
    for r in rankings:
        # Only assign rank if they are not pending (or maybe pending clubs get bottom rank?)
        # SRS FR-07: Highest CPS -> Rank 1. Doesn't mention excluding pending.
        # But FR-12 says "tier is marked as Tier Pending".
        # Assuming pending clubs are still ranked by CPS or excluded?
        # Usually pending means "not yet ranked".
        # Let's rank them by CPS anyway, but they show as Pending Tier.
        if r.tier == 'P':
             r.rank = None # Or maybe put at the bottom?
             # SRS doesn't specify. I'll leave rank as None or just rank them.
             # "System must generate ranked list of clubs".
             # If I have 1 event with 100 CPS, do I beat 2 events with 80 CPS?
             # FR-12 says "A club must complete at least 2 events... to receive a ranking."
             # This implies pending clubs do NOT receive a rank.
             r.rank = None
        else:
            r.rank = current_rank
            current_rank += 1
        r.save()

@receiver(pre_save, sender=Event)
def event_pre_save_handler(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Event.objects.get(pk=instance.pk)
            # Store diff in instance for post_save to use
            changes = []
            for field in ['planning_score', 'execution_score', 'documentation_score', 'innovation_score', 'turnout_score', 'total_score']:
                if field == 'total_score': continue
                old_val = getattr(old_instance, field)
                new_val = getattr(instance, field)
                if old_val != new_val:
                    changes.append(f"{field}: {old_val} -> {new_val}")

            if changes:
                instance._audit_changes = "; ".join(changes)
        except Event.DoesNotExist:
            pass

@receiver(post_save, sender=Event)
def event_save_handler(sender, instance, created, **kwargs):
    action = "Event Added" if created else "Event Updated"
    details = f"Event: {instance.name} ({instance.club.short_code}). Score: {instance.total_score}"

    if not created and hasattr(instance, '_audit_changes'):
        details += f". Changes: {instance._audit_changes}"

    create_audit_log(instance, action, details)

    event_update_handler(instance)

@receiver(post_delete, sender=Event)
def event_delete_handler(sender, instance, **kwargs):
    action = "Event Deleted"
    details = f"Event: {instance.name} ({instance.club.short_code})"
    create_audit_log(instance, action, details)

    event_update_handler(instance)

def event_update_handler(instance):
    club = instance.club
    semester = instance.semester

    # 1. Recalculate CPS/Tier for this club
    calculate_club_performance(club, semester)

    # 2. Update Ranks for the whole semester
    update_semester_ranks(semester)

@receiver(pre_save, sender=Club)
def club_pre_save_handler(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = Club.objects.get(pk=instance.pk)
            changes = []
            for field in ['name', 'short_code', 'faculty_incharge', 'student_lead']:
                old_val = getattr(old_instance, field)
                new_val = getattr(instance, field)
                if old_val != new_val:
                    changes.append(f"{field}: {old_val} -> {new_val}")
            if changes:
                instance._audit_changes = "; ".join(changes)
        except Club.DoesNotExist:
            pass

@receiver(post_save, sender=Club)
def club_save_handler(sender, instance, created, **kwargs):
    if created:
        action = "Club Added"
        details = f"Club: {instance.name}"
    else:
        action = "Club Updated"
        details = f"Club: {instance.name} details updated."
        if hasattr(instance, '_audit_changes'):
            details += f" Changes: {instance._audit_changes}"

    create_audit_log(instance, action, details)
