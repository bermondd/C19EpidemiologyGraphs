if __name__ == "__main__":
    import polars as pl

    locations_index = pl.scan_csv("../input_data/covid19_google/index.csv").select(
        pl.col("location_key"), pl.col("aggregation_level").cast(pl.Int32)
    )

    locations_epidemiology = pl.scan_csv("../input_data/covid19_google/epidemiology.csv").select(
        pl.col("location_key"),
        pl.col("date").cast(pl.Date),
        pl.col("new_confirmed").cast(pl.Int32),
        pl.col("new_deceased").cast(pl.Int32),
        pl.col("new_recovered").cast(pl.Int32),
        pl.col("new_tested").cast(pl.Int32),
        pl.col("cumulative_confirmed").cast(pl.Int64),
        pl.col("cumulative_deceased").cast(pl.Int64),
        pl.col("cumulative_recovered").cast(pl.Int64),
        pl.col("cumulative_tested").cast(pl.Int64)
    ).drop_nulls(
        subset=["location_key", "date"]
    ).join(
        locations_index, on="location_key", how="inner"
    ).sort(by="date").sink_parquet(
        "../intermediate_data/epidemiological_frames/processed_epidemiology.parquet",
        compression="zstd", compression_level=19, engine="streaming"
    )
