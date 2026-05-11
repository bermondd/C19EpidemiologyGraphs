# C19EpidemiologyGraphs
C19EpidemiologyGraphs is a global and multi-aggregation level database of spatial graphs with vertex features pertaining to COVID-19 epidemiology, offered as a SQLite 3 database. This repository hosts this project's source code and final database file.

To build the database, we processed epidemiological data from Google's COVID-19 Open Data Repository (https://health.google.com/covid-19/open-data/) and combined it with geometrical spatial data from GADM (https://gadm.org/), which is used to create the graph edges. More information on the original sources are in the `input_data/README.md` file.

The database is available for download in this repository's releases page (https://github.com/bermondd/C19EpidemiologyGraphs/releases/tag/database-file). Due to GitHub size limits, it's only available as a ZSTD-compressed file. The uncompressed size is 9.4GB, so make sure you have at least that much storage left before decompressing it.

If you want to see an example of how one could use the database to make a Torch Geometric dataset to be used with graph neural networks, check out `example/example_torch_geometric_notebook.ipynb`. That example only goes to the extent of creating a dataset using that library, as training a GNN using it would follow from standard procedures and therefore would be out of our scope.

The processed database file and the source code used to create it are licensed independently: the source code is licensed under BSD-3, as informed by the top-level `LICENSE` file, but the compressed SQLite database file and it's uncompressed counterpart are dual-licensed with CC BY-SA 4.0 (only applicable for graph edges where one or both of it's ends represent an Austrian location) and CC BY 4.0 (applicable for everything else). Further details on this dual-license is in the release page.
