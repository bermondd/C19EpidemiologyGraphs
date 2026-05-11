# Intermediate data
This directory holds intermediate files generated during the data processing.
Each source file is meant to accomplish one specific task, and therefore they were all coded as independent scripts,
rather than modules to be imported. This means their end result need to be written to disk so that the final script
(`populate_database.py`) can read them. This design choice isn't usually the best, but it helped with
debugging in this case and, given this project only has 4 scripts, it's drawbacks were minimal.

This folder has 3 subdirectories:
- epidemiological_frames: Actually only holds 1 parquet file. This is where `process_epidemiological_data.py` writes to.
- full_graphs: Holds 3 big .npz files, which store sparse matrices meant to represent full graphs at 3 levels
of aggregation. This is where `process_spatial_data.py` writes to.
- vertex_info: Holds 3 parquet files, the result of joining the GADM data source with Covid-19 Open Data Repository.
These parquet files hold an association between a full graph's index and an epidemiological source's location key,
alongside some other location-specific information (such as country name, coordinates, etc).
This is where `join_spatial_and_epidemiological_sources.py` writes to.