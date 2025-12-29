from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

class Semester(models.Model):
    name = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Club(models.Model):
    name = models.CharField(max_length=100, unique=True)
    short_code = models.CharField(max_length=10, unique=True)
    faculty_incharge = models.CharField(max_length=100)
    student_lead = models.CharField(max_length=100)
    contact_details = models.TextField()

    def __str__(self):
        return self.name

class Event(models.Model):
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=200)
    date = models.DateField()
    expected_turnout = models.PositiveIntegerField()
    actual_turnout = models.PositiveIntegerField()

    # Metrics
    planning_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    execution_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    documentation_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    innovation_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)])
    turnout_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(20)])

    def __str__(self):
        return f"{self.name} - {self.club.short_code}"

    @property
    def total_score(self):
        return (
            self.planning_score +
            self.execution_score +
            self.documentation_score +
            self.innovation_score +
            self.turnout_score
        )

class Ranking(models.Model):
    TIER_CHOICES = [
        ('A', 'Tier A'),
        ('B', 'Tier B'),
        ('C', 'Tier C'),
        ('D', 'Tier D'),
        ('P', 'Tier Pending'),
    ]

    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='rankings')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='rankings')
    cps = models.FloatField(default=0.0)
    tier = models.CharField(max_length=1, choices=TIER_CHOICES, default='P')
    rank = models.PositiveIntegerField(null=True, blank=True)
    event_count = models.PositiveIntegerField(default=0)

    # Detailed averages for display
    avg_planning = models.FloatField(default=0.0)
    avg_execution = models.FloatField(default=0.0)
    avg_documentation = models.FloatField(default=0.0)
    avg_innovation = models.FloatField(default=0.0)
    avg_turnout = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('club', 'semester')
        ordering = ['rank']

    def __str__(self):
        return f"{self.club.short_code} - {self.semester} (Rank: {self.rank})"

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField()

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
