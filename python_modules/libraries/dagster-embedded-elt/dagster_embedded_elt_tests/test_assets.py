import os
import sqlite3
import tempfile

from dagster import AssetSpec, file_relative_path
from dagster._core.definitions import build_assets_job
from dagster_embedded_elt.sling import SlingMode, SlingResource, build_sling_asset
from dagster_embedded_elt.sling.resources import SlingSourceConnection, SlingTargetConnection


def test_build_sling_asset():
    with tempfile.TemporaryDirectory() as tmpdir_path:
        fpath = os.path.abspath(file_relative_path(__file__, "test.csv"))
        dbpath = os.path.join(tmpdir_path, "sqlite.db")

        sling_resource = SlingResource(
            source_connection=SlingSourceConnection(type="file"),
            target_connection=SlingTargetConnection(
                type="sqlite", connection_string=f"sqlite://{dbpath}"
            ),
        )

        asset_spec = AssetSpec(
            key=["main", "tbl"],
            group_name="etl",
            description="ETL Test",
            deps=["foo"],
        )
        asset_def = build_sling_asset(
            asset_spec=asset_spec,
            source_stream=f"file://{fpath}",
            target_object="main.tbl",
            mode=SlingMode.INCREMENTAL,
            primary_key="SPECIES_CODE",
            sling_resource_key="sling_resource",
        )

        sling_job = build_assets_job(
            "sling_job",
            [asset_def],
            resource_defs={"sling_resource": sling_resource},
        )

        res = sling_job.execute_in_process()
        assert res.success
        counts = sqlite3.connect(dbpath).execute("SELECT count(1) FROM main.tbl").fetchone()
        assert counts[0] == 3
