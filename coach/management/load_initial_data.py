from django.core.management.base import BaseCommand
import json
from coach.models import Professor, Turma, Course, Grade

class Command(BaseCommand):
    help = 'Loads initial data from new_grades.json into the database'

    def handle(self, *args, **options):
        with open('coach/data/new_grades.json', 'r') as f:
            data = json.load(f)

        # Create Turmas
        for turma_data in data.get('turmas', []):
            turma, created = Turma.objects.get_or_create(
                nome=turma_data['nome'],
                defaults={'materias': turma_data.get('materias', [])}
            )

        # Create Professors
        for prof_data in data.get('professors', []):
            professor, created = Professor.objects.get_or_create(
                nome=prof_data['nome'],
                defaults={
                    'materia': prof_data.get('materia', ''),
                    'nota': prof_data.get('nota', 0.0)
                }
            )
            for turma_name in prof_data.get('turmas', []):
                turma = Turma.objects.get(nome=turma_name)
                professor.turmas.add(turma)

        # Update Grades with Turma (optional, based on your data)
        for grade in Grade.objects.all():
            # Logic to assign turma based on username or other criteria
            pass  # Add logic to match grades to turmas if needed

        self.stdout.write(self.style.SUCCESS('Successfully loaded initial data'))