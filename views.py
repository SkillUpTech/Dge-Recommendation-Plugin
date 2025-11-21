from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
import requests
from collections import defaultdict


class RecommendationsView(APIView):
    """
    GET /api/v1/recommendations/student/<student_id>/
    Main endpoint for AI-based course recommendations.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        # 1. Fetch data from AI API
        ai_url = getattr(
            settings,
            "AI_RECOMMENDATION_URL",
            "https://ai-team-api.example.com/api/v1/recommendations",
        )

        try:
            response = requests.get(f"{ai_url}?student_id={student_id}", timeout=5)
            ai_data = response.json().get("recommendations", []) if response.status_code == 200 else []
        except Exception as e:
            print(f"[AI API ERROR] {e}")
            ai_data = []

        # 2. Fetch student metadata (mocked for now)
        enrolled_courses = get_enrolled_courses(student_id)
        student_grade = get_student_grade(student_id)

        # 3. Exclude enrolled courses
        filtered = [
            c for c in ai_data
            if c.get("course_id") not in enrolled_courses
        ]

        # 4. Grade filtering
        if student_grade is not None:
            filtered = [
                c for c in filtered
                if c.get("grade") == student_grade or c.get("grade") == student_grade + 1
            ]

        # 5. Subject balancing (1–3 each, max 10)
        balanced = balance_subjects(filtered)

        # 6. Fallback logic
        if not balanced:
            if student_grade is not None:
                balanced = get_grade_based_courses(student_grade)
            else:
                balanced = get_default_starter_list()

        # 7. Return final response
        return Response(
            {"student_id": student_id, "recommendations": balanced},
            status=status.HTTP_200_OK,
        )


# ------------------------- Helper Functions ----------------------------

def get_enrolled_courses(student_id):
    """
    TODO: Integrate LMS enrollment API.
    """
    return ["course-v1:english101", "course-v1:math999"]


def get_student_grade(student_id):
    """
    TODO: Replace with real student profile API.
    """
    return 8


def get_grade_based_courses(grade):
    """
    Cold-start recommendations when grade is known.
    """
    return [
        {
            "course_id": f"course-v1:math{grade}01",
            "title": f"Math Grade {grade}",
            "subject": "Math",
            "grade": grade,
        },
        {
            "course_id": f"course-v1:science{grade}01",
            "title": f"Science Grade {grade}",
            "subject": "Science",
            "grade": grade,
        },
        {
            "course_id": f"course-v1:english{grade}01",
            "title": f"English Grade {grade}",
            "subject": "English",
            "grade": grade,
        },
    ]


def get_default_starter_list():
    """
    Bare-start fallback (no grade, no activity).
    """
    return [
        {
            "course_id": "course-v1:intro001",
            "title": "Learning Basics",
            "subject": "General",
            "grade": None,
        },
        {
            "course_id": "course-v1:creative002",
            "title": "Creative Thinking",
            "subject": "General",
            "grade": None,
        },
        {
            "course_id": "course-v1:skills003",
            "title": "Study Skills Essentials",
            "subject": "General",
            "grade": None,
        },
    ]


def balance_subjects(courses, per_subject=3, total_limit=10):
    """
    Group by subject and limit 1–3 per subject.
    """
    grouped = defaultdict(list)
    for c in courses:
        grouped[c.get("subject", "Unknown")].append(c)

    final = []
    for subject in sorted(grouped.keys()):
        final.extend(grouped[subject][:per_subject])
        if len(final) >= total_limit:
            break

    return final[:total_limit]
