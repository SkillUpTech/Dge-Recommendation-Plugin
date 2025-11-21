from django.urls import path
from .views import RecommendationsView

urlpatterns = [
    path(
        "student/<str:student_id>/",
        RecommendationsView.as_view(),
        name="ai_recommendations",
    ),
]
