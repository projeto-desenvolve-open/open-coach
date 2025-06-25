# core/coach/migrations/0003_add_professor_and_turma.py
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('coach', '0002_alter_course_server_alter_grade_course_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Professor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100)),
                ('materia', models.CharField(max_length=100)),
                ('nota', models.FloatField()),
            ],
            options={
                'db_table': 'professors',
            },
        ),
        migrations.CreateModel(
            name='Turma',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=100, unique=True)),
                ('materias', models.JSONField(default=list)),
            ],
            options={
                'db_table': 'turmas',
            },
        ),
        migrations.AddField(
            model_name='professor',
            name='turmas',
            field=models.ManyToManyField(to='coach.Turma'),
        ),
        migrations.AddField(
            model_name='grade',
            name='turma',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='coach.Turma'),
        ),
    ]