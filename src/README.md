# Source files
This directory hosts all the source files, of which there are four:
- `process_spatial_data.py`: Script that finds the adjacency list from the GADM polygon shapes.
This creates three big graphs, one for each aggregation level being considered.
- `process_epidemiological_data.py`: Script that runs through the epidemiology file from Google's Covid-19 Open Data
Repository and performs multiple filters and transforms before saving the final result into a parquet file.
Examples of processing steps include interpolation of missing values and aggregating days using a rolling time window.
- `join_spatial_and_epidemiological_sources.py`: Script that creates an association between a location key from
Google's Covid-19 Open Data Repository and a graph node, from the graphs obtained by processing the GADM shapes.
Do note that this is an approximation and is subjected to some errors. Also, we only allowed a 1-to-1 mapping, but this
is not necessarily accurate and could be a point of change. We just thought it would be better to have fewer matches
in total, by not keeping any duplicate matches, than to run a higher risk of incorrect matches. The output of this
file is written into three parquet files, one for each aggregation level.
- `populate_database.py`: Script that creates the C19EpidemiologyGraphs database file and populates it using the
outputs obtained by the three previous scripts. This script needs to be run last, but the 3 scripts above could be
run in any order.