from django.db import models


class Fixture(models.Model):
    team_a = models.CharField(max_length=150)
    team_b = models.CharField(max_length=150)
    score_a = models.CharField(max_length=10, default="0")
    score_b = models.CharField(max_length=10, default="0")

    def __str__(self):
        return f"{self.team_a} score: {self.score_a} vs {self.team_b} score: {self.score_b}"
