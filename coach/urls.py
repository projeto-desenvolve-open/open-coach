from django.urls import path
from . import views

app_name = 'coach'

urlpatterns = [
    path('ping/', views.PingView.as_view(), name='ping'),
    path('student/resources/<str:student_email>/', views.StudentResourcesView.as_view(), name='student_resources'),
    path('student/study-plan/<str:student_email>/', views.StudentStudyPlanView.as_view(), name='student_study_plan'),
    path('student/grades/<str:student_email>/', views.StudentGradesView.as_view(), name='student_grades'),
    path('student/simulado/<str:student_email>/', views.StudentSimuladoView.as_view(), name='student_simulado'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('chat/student/', views.ChatStudentView.as_view(), name='chat_student'),
    path('chat/teacher/', views.ChatTeacherView.as_view(), name='chat_teacher'),
    path('courses/', views.CoursesView.as_view(), name='courses'),
    path('course-content/<str:course_id>/', views.CourseContentView.as_view(), name='course_content'),
    path('grades/<int:student_id>/', views.StudentGradesByIdView.as_view(), name='student_grades_by_id'),
    path('grades/<str:student_email>/<str:course_id>/', views.SpecificStudentGradeView.as_view(), name='specific_student_grade'),
    path('student-grades/<str:student_email>/', views.AllStudentGradesView.as_view(), name='all_student_grades'),
    path('teacher-options/all-grades/', views.AllStudentGradesTeacherView.as_view(), name='all_student_grades_teacher'),
    path('teacher-options/compare-cities/', views.CompareCitiesView.as_view(), name='compare_cities'),
    path('teacher-options/grades-by-username/<str:username>/', views.GradesByUsernameView.as_view(), name='grades_by_username'),
    path('teacher-options/course-content/<str:course_name>/', views.CourseContentTeacherView.as_view(), name='course_content_teacher'),
    path('teacher-options/feedback/<str:username>/<str:course_id>/', views.GenerateFeedbackView.as_view(), name='generate_feedback'),
    path('teacher-options/exercises/<str:username>/<str:course_id>/', views.GenerateExercisesView.as_view(), name='generate_exercises'),
    path('teacher-options/class-exercises/<str:city>/<str:course_name>/', views.GenerateClassExercisesView.as_view(), name='generate_class_exercises'),
    path('teacher-options/grades-by-city/<str:city>/', views.GradesByCityView.as_view(), name='grades_by_city'),
    path('study-plan/', views.StudyPlanView.as_view(), name='study_plan'),
    path('teaching-materials/', views.TeachingMaterialsView.as_view(), name='teaching_materials'),
]