from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Attempt",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("owner", models.CharField(db_index=True, max_length=32)),
                ("questions", models.JSONField()),
                ("answers", models.JSONField(default=dict)),
                ("submitted", models.BooleanField(default=False)),
                ("short_override", models.BooleanField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("number", models.PositiveIntegerField(unique=True)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("easy", "하"),
                            ("medium", "중"),
                            ("hard", "상"),
                            ("short", "단답형"),
                        ],
                        max_length=10,
                    ),
                ),
                ("text", models.TextField()),
                ("choices", models.JSONField(blank=True, default=list)),
                (
                    "correct_choice",
                    models.PositiveSmallIntegerField(blank=True, null=True),
                ),
                ("answer", models.TextField()),
                ("explanation", models.TextField()),
                ("source", models.CharField(max_length=200)),
                ("accepted_answers", models.JSONField(blank=True, default=list)),
                ("keyword_groups", models.JSONField(blank=True, default=list)),
            ],
        ),
    ]
