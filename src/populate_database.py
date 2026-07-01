if __name__ == "__main__":
    from tqdm import tqdm
    import polars as pl
    import sqlite3
    import torch
    import torch_geometric as tg
    from scipy.sparse import load_npz
    from geographiclib.geodesic import Geodesic

    con = sqlite3.connect("../C19EpidemiologyGraphs.sqlite3")
    cur = con.cursor()

    # Create all the tables
    cur.execute("""
        CREATE TABLE vertices (
            location_key TEXT PRIMARY KEY,
            aggregation_level INT NOT NULL,
            GADM_layer INT NOT NULL,
            GADM_index INT NOT NULL,
            country_name TEXT NOT NULL,
            subregion1_name TEXT,
            subregion2_name TEXT,
            y_latitude REAL NOT NULL,
            x_longitude REAL NOT NULL,
            UNIQUE (aggregation_level, GADM_layer, GADM_index),
            CHECK (aggregation_level IN (0, 1, 2)),
            CHECK (GADM_layer IN (0, 1, 2, 3)),
            CHECK (GADM_index >= 0)
        ) STRICT;
    """)
    cur.execute("""
        CREATE TABLE edges (
            source TEXT,
            destination TEXT,
            distance_m REAL NOT NULL,
            PRIMARY KEY (source, destination),
            FOREIGN KEY (source) REFERENCES vertices (location_key),
            FOREIGN KEY (destination) REFERENCES vertices(location_key),
            CHECK (distance_m >= 0)
        ) STRICT;
    """)
    cur.execute("""
        CREATE TABLE epidemiology (
            location_key TEXT,
            date INT,
            new_confirmed INT,
            new_deceased INT,
            new_recovered INT,
            new_tested INT,
            cumulative_confirmed INT,
            cumulative_deceased INT,
            cumulative_recovered INT,
            cumulative_tested INT,
            PRIMARY KEY(location_key, date),
            FOREIGN KEY (location_key) REFERENCES vertices(location_key)
        ) STRICT;
    """)


    # Insert vertices
    curr_graph_matrix = load_npz("../intermediate_data/full_graphs/full_gadm_graph_level_0.npz")
    graph_0 = tg.data.Data(x=torch.arange(curr_graph_matrix.shape[0], dtype=torch.int32).unsqueeze(1),
                           edge_index=tg.utils.from_scipy_sparse_matrix(curr_graph_matrix)[0])

    curr_graph_matrix = load_npz("../intermediate_data/full_graphs/full_gadm_graph_level_1.npz")
    graph_1 = tg.data.Data(x=torch.arange(curr_graph_matrix.shape[0], dtype=torch.int32).unsqueeze(1),
                           edge_index=tg.utils.from_scipy_sparse_matrix(curr_graph_matrix)[0])

    curr_graph_matrix = load_npz("../intermediate_data/full_graphs/full_gadm_graph_level_2.npz")
    graph_2 = tg.data.Data(x=torch.arange(curr_graph_matrix.shape[0], dtype=torch.int32).unsqueeze(1),
                           edge_index=tg.utils.from_scipy_sparse_matrix(curr_graph_matrix)[0])

    full_graphs = tg.data.Data(x=torch.arange(graph_0.num_nodes + graph_1.num_nodes + graph_2.num_nodes,
                                              dtype=torch.int32),
                               edge_index=torch.cat([graph_0.edge_index,
                                                     graph_1.edge_index + graph_0.num_nodes,
                                                     graph_2.edge_index + graph_0.num_nodes + graph_1.num_nodes],
                                                    dim=1)).coalesce()

    vertex_info_0 = pl.scan_parquet(
        "../intermediate_data/vertex_info/vertex_info_level_0.parquet"
    ).with_columns(
        aggregation_level=0,
        subregion1_name=pl.lit(None, dtype=pl.String),
        subregion2_name=pl.lit(None, dtype=pl.String)
    ).select("graph_node_index", "location_key", "aggregation_level", "GADM_layer", "GADM_key",
             "country_name", "subregion1_name", "subregion2_name", "latitude", "longitude")

    vertex_info_1 = pl.scan_parquet(
        "../intermediate_data/vertex_info/vertex_info_level_1.parquet"
    ).with_columns(
        graph_node_index=pl.col("graph_node_index") + graph_0.num_nodes,
        aggregation_level=1,
        subregion2_name=pl.lit(None, dtype=pl.String)
    ).select("graph_node_index", "location_key", "aggregation_level", "GADM_layer", "GADM_key",
             "country_name", "subregion1_name", "subregion2_name", "latitude", "longitude")

    vertex_info_2 = pl.scan_parquet(
        "../intermediate_data/vertex_info/vertex_info_level_2.parquet"
    ).with_columns(
        graph_node_index=pl.col("graph_node_index") + graph_0.num_nodes + graph_1.num_nodes,
        aggregation_level=2,
    ).select("graph_node_index", "location_key", "aggregation_level", "GADM_layer", "GADM_key",
             "country_name", "subregion1_name", "subregion2_name", "latitude", "longitude")

    vs = pl.concat(
        [vertex_info_0, vertex_info_1, vertex_info_2]
    ).unique("graph_node_index", keep="none").collect(engine="streaming")

    cur.executemany("INSERT INTO vertices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                    vs.select(pl.exclude("graph_node_index")).rows())

    # Required auxiliary dictionary mapping graph node indices to location keys
    # https://stackoverflow.com/a/75994185
    index_to_location_map = dict(vs.select("graph_node_index", "location_key").iter_rows())

    # Insert edges
    edge_list = []
    for [source, destination] in tqdm(full_graphs.edge_index.T.tolist()):
        if source not in index_to_location_map or destination not in index_to_location_map:
            continue
        source_key = index_to_location_map[source]
        destination_key = index_to_location_map[destination]
        lat1, lon1 = cur.execute(
            "SELECT y_latitude, x_longitude FROM vertices WHERE location_key = ?;",
            [source_key]).fetchone()
        lat2, lon2 = cur.execute(
            "SELECT y_latitude, x_longitude FROM vertices WHERE location_key = ?;",
            [destination_key]).fetchone()
        dist_m = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2)["s12"]
        edge_list.append((source_key, destination_key, dist_m))
    cur.executemany("INSERT INTO edges VALUES (?, ?, ?);", edge_list)

    # Insert epidemiological entries
    filter_series = vs.get_column("location_key").implode()
    epidemiologic_df = pl.scan_parquet(
        "../intermediate_data/epidemiological_frames/processed_epidemiology.parquet"
    ).filter(
        pl.col("location_key").is_in(filter_series)
    ).select(
        "location_key", pl.col("date").cast(pl.Int32),
        "new_confirmed", "new_deceased", "new_recovered", "new_tested",
        "cumulative_confirmed", "cumulative_deceased", "cumulative_recovered", "cumulative_tested"
    ).collect(engine="streaming")

    n_rows_per_slice = 100_000
    total_tqdm = (len(epidemiologic_df) // n_rows_per_slice) + int(len(epidemiologic_df) % n_rows_per_slice != 0)
    for frame in tqdm(epidemiologic_df.iter_slices(n_rows_per_slice), total=total_tqdm):
        cur.executemany("""
            INSERT INTO epidemiology (
                location_key, date,
                new_confirmed, new_deceased, new_recovered, new_tested,
                cumulative_confirmed, cumulative_deceased, cumulative_recovered, cumulative_tested,
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, frame.rows())

    # Commit changes to the database file and close the connections
    con.commit()
    cur.close()
    con.close()

