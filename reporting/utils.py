from django.db.models import F, Sum, Count, FloatField

from iteration.models import Iteration
from story.models import Story, VerifiedByUser
from task.models import Task


def generate_month_report(start_date, end_date, session):
    """
    Generate the monthly report for a season.
    Saves JSON into session.report_data.
    """

    # Iterations inside the month
    iterations = Iteration.objects.filter(
        start_date__gte=start_date,
        end_date__lte=end_date,
        is_active=True,
        team_id=session.team_id if hasattr(session, "team_id") else None
    )

    # Completed stories inside these iterations
    stories = Story.objects.filter(
        iteration__in=iterations,
        status=Story.STATUS_COMPLETED,
        is_active=True
    )

    # Completed tasks inside these iteration and stories
    tasks = Task.objects.filter(
        story__in=stories,
        status=Task.STATUS_COMPLETE,
        is_active=True
    )

    # Total number of iteration
    total_iteration = iterations.count()

    # Total number of story
    total_story = stories.count()

    # Contributed Project (sum of hours)
    top_project = (
        stories.values(
            "project__id",
            project_name=F("project__name"),
        )
        .annotate(total_hours=Sum("total_estimate_time", output_field=FloatField()))
        .order_by("-total_hours")
    )

    # Total tasks done by users
    total_tasks_by_users = (
        tasks.values(
            "user_id",
            fullname=F("user__fullname")
        )
        .annotate(total_tasks=Count("id"))
        .order_by("-total_tasks")
    )

    # Total hour committed by users
    total_hours_committed_by_user = (
        tasks.values(
            "user_id",
            fullname=F("user__fullname")
        )
        .annotate(total_hour=Sum("estimate_time", output_field=FloatField()))
        .order_by("-total_hour")
    )

    # Total solo task
    total_solo_by_users = (
        tasks.values(
            "user_id",
            fullname=F("user__fullname")
        )
        .filter(story__is_multi=False)
        .annotate(total_solo=Count("id"))
        .order_by("-total_solo")
    )

    # Total RnD tasks
    total_rnd_by_users = (
        tasks.values(
            "user_id",
            fullname=F("user__fullname")
        )
        .filter(story__is_rnd=True)
        .annotate(total_rnd=Count("id"))
        .order_by("-total_rnd")
    )

    # Verified tasks by users
    total_verified_by_users = (
        VerifiedByUser.objects.values(
            "user_id",
            fullname=F("user__fullname")
        )
        .filter(story__in=stories)
        .annotate(total_verified=Count("id"))
        .order_by("-total_verified")
    )

    # Bugs created by users
    total_bug_by_users = (
        tasks.values(
            "user_id",
            fullname=F("user__fullname")
        )
        .filter(is_bug=True)
        .annotate(total_bug=Count("id"))
        .order_by("-total_bug")
    )

    # Final result
    result = {
        "total_iteration": total_iteration,
        "total_story": total_story,
        "top_projects": list(top_project),
        "total_tasks_by_users": list(total_tasks_by_users),
        "total_hours_committed_by_user": list(total_hours_committed_by_user),
        "total_solo_by_users": list(total_solo_by_users),
        "total_rnd_by_users": list(total_rnd_by_users),
        "total_verified_by_users": list(total_verified_by_users),
        "total_bug_by_users": list(total_bug_by_users),
    }

    # Save into session model
    session.report_data = result  
    session.save()

    return result
