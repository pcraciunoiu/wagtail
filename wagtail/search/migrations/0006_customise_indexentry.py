# Generated by Django 3.2.4 on 2021-07-12 22:49

from django.db import connection, migrations, models

from wagtail.search.models import IndexEntry


# This migration takes on the base model defined in 0005_create_indexentry and adds certain fields that are specific to each database system
class Migration(migrations.Migration):

    dependencies = [
        ("wagtailsearch", "0005_create_indexentry"),
    ]

    if connection.vendor == "postgresql":
        import django.contrib.postgres.indexes
        import django.contrib.postgres.search

        operations = [
            migrations.AddField(
                model_name="indexentry",
                name="autocomplete",
                field=django.contrib.postgres.search.SearchVectorField(),
            ),
            migrations.AddField(
                model_name="indexentry",
                name="title",
                field=django.contrib.postgres.search.SearchVectorField(),
            ),
            migrations.AddField(
                model_name="indexentry",
                name="body",
                field=django.contrib.postgres.search.SearchVectorField(),
            ),
            migrations.AddIndex(
                model_name="indexentry",
                index=django.contrib.postgres.indexes.GinIndex(
                    fields=["autocomplete"], name="wagtailsear_autocom_476c89_gin"
                ),
            ),
            migrations.AddIndex(
                model_name="indexentry",
                index=django.contrib.postgres.indexes.GinIndex(
                    fields=["title"], name="wagtailsear_title_9caae0_gin"
                ),
            ),
            migrations.AddIndex(
                model_name="indexentry",
                index=django.contrib.postgres.indexes.GinIndex(
                    fields=["body"], name="wagtailsear_body_90c85d_gin"
                ),
            ),
        ]

    elif connection.vendor == "sqlite":
        from wagtail.search.backends.database.sqlite.utils import fts5_available

        operations = [
            migrations.AddField(
                model_name="indexentry",
                name="autocomplete",
                field=models.TextField(null=True),
            ),
            migrations.AddField(
                model_name="indexentry",
                name="body",
                field=models.TextField(null=True),
            ),
            migrations.AddField(
                model_name="indexentry",
                name="title",
                field=models.TextField(),
            ),
        ]

        if fts5_available():
            operations.append(
                migrations.SeparateDatabaseAndState(
                    state_operations=[
                        migrations.CreateModel(
                            name="sqliteftsindexentry",
                            fields=[
                                (
                                    "index_entry",
                                    models.OneToOneField(
                                        primary_key=True,
                                        serialize=False,
                                        to="wagtailsearch.indexentry",
                                        on_delete=models.CASCADE,
                                        db_column="rowid",
                                    ),
                                ),
                                ("title", models.TextField()),
                                ("body", models.TextField(null=True)),
                                ("autocomplete", models.TextField(null=True)),
                            ],
                            options={"db_table": "%s_fts" % IndexEntry._meta.db_table},
                        ),
                    ],
                    database_operations=[
                        migrations.RunSQL(
                            sql=(
                                "CREATE VIRTUAL TABLE %s_fts USING fts5(autocomplete, body, title)"
                                % IndexEntry._meta.db_table
                            ),
                            reverse_sql=(
                                "DROP TABLE IF EXISTS %s_fts"
                                % IndexEntry._meta.db_table
                            ),
                        ),
                        migrations.RunSQL(
                            sql=(
                                "CREATE TRIGGER insert_wagtailsearch_indexentry_fts AFTER INSERT ON %s BEGIN INSERT INTO %s_fts(title, body, autocomplete, rowid) VALUES (NEW.title, NEW.body, NEW.autocomplete, NEW.id); END"
                                % (IndexEntry._meta.db_table, IndexEntry._meta.db_table)
                            ),
                            reverse_sql=(
                                "DROP TRIGGER IF EXISTS insert_wagtailsearch_indexentry_fts"
                            ),
                        ),
                        migrations.RunSQL(
                            sql=(
                                "CREATE TRIGGER update_wagtailsearch_indexentry_fts AFTER UPDATE ON %s BEGIN UPDATE %s_fts SET title=NEW.title, body=NEW.body, autocomplete=NEW.autocomplete WHERE rowid=NEW.id; END"
                                % (IndexEntry._meta.db_table, IndexEntry._meta.db_table)
                            ),
                            reverse_sql=(
                                "DROP TRIGGER IF EXISTS update_wagtailsearch_indexentry_fts"
                            ),
                        ),
                        migrations.RunSQL(
                            sql=(
                                "CREATE TRIGGER delete_wagtailsearch_indexentry_fts AFTER DELETE ON %s BEGIN DELETE FROM %s_fts WHERE rowid=OLD.id; END"
                                % (IndexEntry._meta.db_table, IndexEntry._meta.db_table)
                            ),
                            reverse_sql=(
                                "DROP TRIGGER IF EXISTS delete_wagtailsearch_indexentry_fts"
                            ),
                        ),
                    ],
                )
            )

    elif connection.vendor == "mysql":
        operations = [
            migrations.AddField(
                model_name="indexentry",
                name="autocomplete",
                field=models.TextField(null=True),
            ),
            migrations.AddField(
                model_name="indexentry",
                name="body",
                field=models.TextField(null=True),
            ),
            migrations.AddField(
                model_name="indexentry",
                name="title",
                field=models.TextField(default=""),
                preserve_default=False,
            ),
        ]

        # Create FULLTEXT indexes
        # We need to add these indexes manually because Django imposes an artificial limitation
        # that forces to specify the max length of the TextFields that get referenced by the
        # FULLTEXT index. If we do it manually, it works, because Django can't check that we are
        # defining a new index.
        operations.append(
            migrations.RunSQL(
                sql="""
                ALTER TABLE wagtailsearch_indexentry
                    ADD FULLTEXT INDEX `fulltext_body` (`body`)
                """,
                reverse_sql="""
                ALTER TABLE wagtailsearch_indexentry
                    DROP INDEX `fulltext_body`
                """,
            )
        )

        # We create two separate FULLTEXT indexes for the 'body' and 'title' columns, so that we are able to handle them separately afterwards.
        # We handle them separately, for example, when we do scoring: there, we multiply the 'title' score by the value of the 'title_norm' column. This can't be done if we index 'title' and 'body' in the same index, because MySQL doesn't allow to search on subparts of a defined index (we need to search all the columns of the index at the same time).
        operations.append(
            migrations.RunSQL(
                sql="""
                ALTER TABLE wagtailsearch_indexentry
                    ADD FULLTEXT INDEX `fulltext_title` (`title`)
                """,
                reverse_sql="""
                ALTER TABLE wagtailsearch_indexentry
                    DROP INDEX `fulltext_title`
                """,
            )
        )

        # We also need to create a joint index on 'title' and 'body', to be able to query both at the same time. If we don't have this, some queries may return wrong results. For example, if we match 'A AND (NOT B)' against 'A, B', it returns false, but if we do (match 'A AND (NOT B)' against 'A') or (match 'A AND (NOT B)' against 'B'), the first one would return True, and the whole expression would be True (wrong result). That's the same as saying that testing subsets does not necessarily produce the same result as testing the whole set.
        operations.append(
            migrations.RunSQL(
                sql="""
                ALTER TABLE wagtailsearch_indexentry
                    ADD FULLTEXT INDEX `fulltext_title_body` (`title`, `body`)
                """,
                reverse_sql="""
                ALTER TABLE wagtailsearch_indexentry
                    DROP INDEX `fulltext_title_body`
                """,
            )
        )

        # We use an ngram parser for autocomplete, so that it matches partial search queries.
        # The index on body and title doesn't match partial queries by default.
        # Note that this is not supported on MariaDB. See https://jira.mariadb.org/browse/MDEV-10267
        if connection.mysql_is_mariadb:
            operations.append(
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE wagtailsearch_indexentry
                        ADD FULLTEXT INDEX `fulltext_autocomplete` (`autocomplete`)
                    """,
                    reverse_sql="""
                    ALTER TABLE wagtailsearch_indexentry
                        DROP INDEX `fulltext_autocomplete`
                    """,
                )
            )
        else:
            operations.append(
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE wagtailsearch_indexentry
                        ADD FULLTEXT INDEX `fulltext_autocomplete` (`autocomplete`)
                        WITH PARSER ngram
                    """,
                    reverse_sql="""
                    ALTER TABLE wagtailsearch_indexentry
                        DROP INDEX `fulltext_autocomplete`
                    """,
                )
            )
