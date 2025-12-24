from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, F
from .models import Club, Ranking, Semester, Event
import csv
from django.http import HttpResponse

class DashboardView(LoginRequiredMixin, ListView):
    model = Ranking
    template_name = 'core/dashboard.html'
    context_object_name = 'rankings'

    def get_queryset(self):
        semester_id = self.request.GET.get('semester')
        # Use F() expression to sort NULL ranks (Pending) last
        qs = Ranking.objects.none()

        if semester_id:
            qs = Ranking.objects.filter(semester__id=semester_id)
        else:
            # Default to most recent or active semester
            active_semester = Semester.objects.filter(is_active=True).first()
            if active_semester:
                 qs = Ranking.objects.filter(semester=active_semester)
            else:
                # Fallback to any semester
                latest_semester = Semester.objects.last()
                if latest_semester:
                     qs = Ranking.objects.filter(semester=latest_semester)

        return qs.order_by(F('rank').asc(nulls_last=True), '-cps')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['semesters'] = Semester.objects.all()
        selected_semester_id = self.request.GET.get('semester')
        if selected_semester_id:
            # Use filter().first() to avoid 500 error if ID is invalid
            context['selected_semester'] = Semester.objects.filter(id=selected_semester_id).first()
        elif Semester.objects.filter(is_active=True).exists():
            context['selected_semester'] = Semester.objects.filter(is_active=True).first()
        else:
            context['selected_semester'] = Semester.objects.last()
        return context

class ClubDetailView(LoginRequiredMixin, DetailView):
    model = Club
    template_name = 'core/club_detail.html'
    context_object_name = 'club'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        semester_id = self.request.GET.get('semester')

        if semester_id:
            semester = get_object_or_404(Semester, id=semester_id)
        else:
             # Default logic same as dashboard
            semester = Semester.objects.filter(is_active=True).first() or Semester.objects.last()

        context['selected_semester'] = semester
        context['semesters'] = Semester.objects.all()

        if semester:
            context['ranking'] = Ranking.objects.filter(club=self.object, semester=semester).first()
            context['events'] = Event.objects.filter(club=self.object, semester=semester)

        return context

def export_rankings_csv(request):
    semester_id = request.GET.get('semester')
    if not semester_id:
        return HttpResponse("Semester not specified", status=400)

    semester = get_object_or_404(Semester, id=semester_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="rankings_{semester.name}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Rank', 'Club', 'CPS', 'Tier', 'Events', 'Avg Planning', 'Avg Execution', 'Avg Doc', 'Avg Innovation', 'Avg Turnout'])

    rankings = Ranking.objects.filter(semester=semester).order_by('rank')
    for r in rankings:
        writer.writerow([
            r.rank if r.rank else 'Pending',
            r.club.name,
            f"{r.cps:.2f}",
            r.tier,
            r.event_count,
            f"{r.avg_planning:.2f}",
            f"{r.avg_execution:.2f}",
            f"{r.avg_documentation:.2f}",
            f"{r.avg_innovation:.2f}",
            f"{r.avg_turnout:.2f}",
        ])

    return response
