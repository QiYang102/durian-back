"""loyalty_reward URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url

from rest_framework.routers import DefaultRouter

from core.views import CustomRefreshTokenView, UserRegisterView, UserViewSet, empty_view, FeatureViewSet, FeatureAccessViewSet
from eventcalendar.views import EventCalendarViewSet
from iteration.views import IterationViewSet
from project.views import ProjectViewSet
from reporting.views import bugs_count_pie_chart, burndown_chart, effort_hour_by_user, first_user_achieve_effort, iteration_total_efforts, pie_chart, pie_chart_projects, project_story_reporting, user_capacity_by_iteration, user_incomplete_story, user_monthly_effort, velocity_chart, user_task_statistics, season_summary, hours_burndown_chart, capacity_reporting
from story.views import StoryImageViewSet, StoryViewSet, VerifiedByUserViewSet, TagViewSet, TagItemViewSet
from task.views import TaskHourViewSet, TaskImageViewSet, TaskTemplateItemViewSet, TaskTemplateViewSet, TaskViewSet
from team.views import TeamMemberViewSet, TeamViewSet
from kopirecord.views import KopiRecordViewSet
from reporting.views import SeasonViewSet
from django.views.decorators.csrf import csrf_exempt
from announcement.views import AnnouncementViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r'users', UserViewSet)
router.register(r'features', FeatureViewSet)
router.register(r'feature-accesses', FeatureAccessViewSet)
router.register(r'rest-auth/registration', UserRegisterView, basename='public-user-registration')
router.register(r'teams', TeamViewSet)
router.register(r'team-members', TeamMemberViewSet)
router.register(r'iterations', IterationViewSet)
router.register(r'tags', TagViewSet)
router.register(r'stories', StoryViewSet)
router.register(r'tag-items', TagItemViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'task-hours', TaskHourViewSet)
router.register(r'task-images', TaskImageViewSet, basename='task-image')

from durian_store.views import CategoryViewSet, ProductViewSet, PromoCodeViewSet, OrderViewSet
router.register(r'durian/categories', CategoryViewSet, basename='durian-category')
router.register(r'durian/products', ProductViewSet, basename='durian-product')
router.register(r'durian/promo-codes', PromoCodeViewSet, basename='durian-promo-code')
router.register(r'durian/orders', OrderViewSet, basename='durian-order')
router.register(r'story-images', StoryImageViewSet, basename='story-image')
router.register(r'task-templates', TaskTemplateViewSet)
router.register(r'task-template-items', TaskTemplateItemViewSet)
router.register(r'event-calendars', EventCalendarViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'kopibeng', KopiRecordViewSet)
router.register(r'season-session', SeasonViewSet)
router.register(r'announcements', AnnouncementViewSet)
router.register(r'verified-by-users', VerifiedByUserViewSet)

api_url = 'v1/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/reset-password/<uidb64>/<token>/',
         empty_view, name='password_reset_confirm'),
    path(api_url, include(router.urls)),
    path(api_url + 'rest-auth/', include('dj_rest_auth.urls')),
    path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    url(api_url + 'api-token-refresh/', CustomRefreshTokenView.as_view(), name='token_refresh'),
    path(api_url + 'reporting/velocity-chart/', velocity_chart, name='velocity_chart'),
    path(api_url + 'reporting/burndown-chart/', burndown_chart, name='burndown_chart'),
    path(api_url + 'reporting/pie-chart/', pie_chart, name='pie_chart'),
    path(api_url + 'reporting/pie-chart-projects/', pie_chart_projects, name='pie_chart_projects'),
    path(api_url + 'reporting/iteration-total-efforts/', iteration_total_efforts, name='iteration_total_efforts'),
    path(api_url + 'reporting/user-incomplete-story/', user_incomplete_story, name='user_incomplete_story'),
    path(api_url + 'reporting/effort-hour-by-user/', effort_hour_by_user, name='effort_hour_by_user'),
    path(api_url + 'reporting/user-capacity-by-iteration/', user_capacity_by_iteration, name='user_capacity_by_iteration'),
    path(api_url + 'reporting/user-monthly-effort/', user_monthly_effort, name='user_monthly_effort'),
    path(api_url + 'reporting/bugs-count-pie-chart/', bugs_count_pie_chart, name='bugs_count_pie_chart'),
    path(api_url + 'task-images/upload-image/', csrf_exempt(TaskImageViewSet.uploadImage), name='uploadImage'),
    path(api_url + 'story-images/story-upload-image/', csrf_exempt(StoryImageViewSet.storyUploadImage), name='storyUploadImage'),
    path(api_url + 'iterations/move-tasks/', csrf_exempt(IterationViewSet.moveTasks), name='moveTasks'),
    path(api_url + 'reporting/first-user-achieve-effort/', first_user_achieve_effort, name='first_user_achieve_effort'),
    path(api_url + 'reporting/user-task-statistics/', user_task_statistics, name='user_task_statistics'),
    path(api_url + 'reporting/project-story-reporting/', project_story_reporting, name='project-story-reporting'),
    path(api_url + 'reporting/hours-burndown-chart/', hours_burndown_chart, name='hours_burndown_chart'),
    path(api_url + 'reporting/capacity-reporting', capacity_reporting, name='capacity_reporting'),
    # path(api_url + 'reporting/season-summary/', season_summary, name='season-summary'),
    




] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
