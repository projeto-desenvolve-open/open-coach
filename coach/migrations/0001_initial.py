from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('course_id', models.CharField(max_length=100, primary_key=True, serialize=False)),
                ('course_name', models.CharField(max_length=200)),
                ('server', models.CharField(max_length=200)),
            ],
            options={
                'db_table': 'courses',
            },
        ),
        migrations.CreateModel(
            name='Grade',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ('user_id', models.IntegerField()),
                ('username', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('calculated_grade', models.FloatField()),
                ('section_breakdown', models.JSONField(default=list)),
                ('course', models.ForeignKey(on_delete=models.CASCADE, to='coach.course')),
            ],
            options={
                'db_table': 'grades',
            },
        ),
    ]