from django.db import models

class Course(models.Model):
    course_id = models.CharField(max_length=100, primary_key=True)
    course_name = models.CharField(max_length=200)
    server = models.CharField(max_length=100)

    def __str__(self):
        return self.course_name

class Grade(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    user_id = models.IntegerField()
    username = models.CharField(max_length=100)
    email = models.EmailField()
    calculated_grade = models.FloatField()
    section_breakdown = models.JSONField(default=list)

    class Meta:
        unique_together = ['course', 'user_id']

    def __str__(self):
        return f"{self.username} - {self.course.course_name} - {self.calculated_grade}"