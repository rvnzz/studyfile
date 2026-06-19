from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0002_remove_assignment_target_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="submission",
            name="ai_grade",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=5,
                null=True,
                verbose_name="Оценка AI",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="ai_feedback",
            field=models.TextField(blank=True, verbose_name="Фидбек AI"),
        ),
        migrations.AddField(
            model_name="submission",
            name="ai_status",
            field=models.CharField(
                blank=True,
                choices=[
                    ("pending", "Ожидает"),
                    ("processing", "Обрабатывается"),
                    ("completed", "Завершено"),
                    ("failed", "Ошибка"),
                ],
                default="",
                max_length=20,
                verbose_name="Статус AI",
            ),
        ),
        migrations.AddField(
            model_name="submission",
            name="ai_graded_at",
            field=models.DateTimeField(
                blank=True, null=True, verbose_name="AI оценено"
            ),
        ),
    ]
