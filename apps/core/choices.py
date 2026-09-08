from django.db import models


class TestType(models.TextChoices):
    
    TEST_PROJECT = "test_project", "Test Project"
    INTERVIEW = "interview", "Interview"