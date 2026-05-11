import polars as pl


def process_windows(epidemiology_df: pl.LazyFrame, window_size: int) -> pl.LazyFrame:
    return epidemiology_df.rolling(
        index_column="date", period=str(window_size) + "d",
        group_by="location_key"
    ).agg(
        true_new_confirmed=pl.when(
            pl.col("true_new_confirmed").count() > 0
        ).then(pl.col("true_new_confirmed").sum()),
        true_new_deceased=pl.when(
            pl.col("true_new_deceased").count() > 0
        ).then(pl.col("true_new_deceased").sum()),
        true_new_recovered=pl.when(
            pl.col("true_new_recovered").count() > 0
        ).then(pl.col("true_new_recovered").sum()),
        true_new_tested=pl.when(
            pl.col("true_new_tested").count() > 0
        ).then(pl.col("true_new_tested").sum()),
        interpolated_new_confirmed=pl.when(
            pl.col("interpolated_new_confirmed").count() > 0
        ).then(pl.col("interpolated_new_confirmed").sum()),
        interpolated_new_deceased=pl.when(
            pl.col("interpolated_new_deceased").count() > 0
        ).then(pl.col("interpolated_new_deceased").sum()),
        interpolated_new_recovered=pl.when(
            pl.col("interpolated_new_recovered").count() > 0
        ).then(pl.col("interpolated_new_recovered").sum()),
        interpolated_new_tested=pl.when(
            pl.col("interpolated_new_tested").count() > 0
        ).then(pl.col("interpolated_new_tested").sum()),
        cumulative_confirmed=pl.col("cumulative_confirmed").last(ignore_nulls=True),
        cumulative_deceased=pl.col("cumulative_deceased").last(ignore_nulls=True),
        cumulative_recovered=pl.col("cumulative_recovered").last(ignore_nulls=True),
        cumulative_tested=pl.col("cumulative_tested").last(ignore_nulls=True),
        num_non_nulls_in_true_confirmed=pl.col("true_new_confirmed").is_not_null().sum(),
        num_non_nulls_in_true_deceased=pl.col("true_new_deceased").is_not_null().sum(),
        num_non_nulls_in_true_recovered=pl.col("true_new_recovered").is_not_null().sum(),
        num_non_nulls_in_true_tested=pl.col("true_new_tested").is_not_null().sum(),
        num_non_nulls_in_interpolated_confirmed=pl.col("interpolated_new_confirmed").is_not_null().sum(),
        num_non_nulls_in_interpolated_deceased=pl.col("interpolated_new_deceased").is_not_null().sum(),
        num_non_nulls_in_interpolated_recovered=pl.col("interpolated_new_recovered").is_not_null().sum(),
        num_non_nulls_in_interpolated_tested=pl.col("interpolated_new_tested").is_not_null().sum(),
        window_size=window_size
    )


if __name__ == "__main__":
    locations_index = pl.scan_csv("../input_data/covid19_google/index.csv").select(
        pl.col("location_key"), pl.col("aggregation_level").cast(pl.Int32)
    )

    locations_epidemiology = pl.scan_csv("../input_data/covid19_google/epidemiology.csv").select(
        pl.col("location_key"),
        pl.col("date").cast(pl.Date),
        pl.col("new_confirmed").cast(pl.Int32).alias("true_new_confirmed"),
        pl.col("new_deceased").cast(pl.Int32).alias("true_new_deceased"),
        pl.col("new_recovered").cast(pl.Int32).alias("true_new_recovered"),
        pl.col("new_tested").cast(pl.Int32).alias("true_new_tested"),
        pl.col("cumulative_confirmed").cast(pl.Int64),
        pl.col("cumulative_deceased").cast(pl.Int64),
        pl.col("cumulative_recovered").cast(pl.Int64),
        pl.col("cumulative_tested").cast(pl.Int64)
    ).drop_nulls(subset=["location_key", "date"]).sort(by="date").with_columns(
        interpolated_new_confirmed=pl.col("true_new_confirmed").interpolate().over(
            partition_by="location_key", order_by="date"
        ).round(decimals=0, mode="half_away_from_zero").cast(pl.Int32),
        interpolated_new_deceased=pl.col("true_new_deceased").interpolate().over(
            partition_by="location_key", order_by="date"
        ).round(decimals=0, mode="half_away_from_zero").cast(pl.Int32),
        interpolated_new_recovered=pl.col("true_new_recovered").interpolate().over(
            partition_by="location_key", order_by="date"
        ).round(decimals=0, mode="half_away_from_zero").cast(pl.Int32),
        interpolated_new_tested=pl.col("true_new_tested").interpolate().over(
            partition_by="location_key", order_by="date"
        ).round(decimals=0, mode="half_away_from_zero").cast(pl.Int32),
    )

    pl.concat(
        [process_windows(locations_epidemiology, size) for size in [1, 3, 5, 7, 10, 15, 30, 60, 90, 180]]
    ).join(locations_index, on="location_key", how="inner").sink_parquet(
        "../intermediate_data/epidemiological_frames/processed_epidemiology.parquet",
        compression="zstd", compression_level=19, engine="streaming")
