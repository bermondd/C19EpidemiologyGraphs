if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    import polars as pl
    import geopandas as gpd
    from shapely.geometry import Point
    from process_spatial_data import agg1_gadm_levels, agg2_gadm_levels

    # geographical axis according to a cartesian plane
    x_key = "longitude"
    y_key = "latitude"

    locations_geography = pd.read_csv("../input_data/covid19_google/geography.csv")
    locations_geography_points = gpd.GeoSeries([Point(x, y) for x, y in zip(locations_geography[x_key],
                                                                            locations_geography[y_key])])
    locations_geography = gpd.GeoDataFrame(locations_geography, crs="EPSG:4326", geometry=locations_geography_points)
    locations_geography["location_key"] = locations_geography["location_key"].astype(str)
    locations_index = pd.read_csv("../input_data/covid19_google/index.csv")
    locations_geo_and_index = gpd.GeoDataFrame(locations_index.merge(locations_geography, on="location_key"))


    geo_infos = [gpd.read_file("../input_data/geodata_gadm/gadm_410-levels.zip", layer="ADM_0")]
    geo_infos[-1]["layer"] = 0
    geo_infos[-1].set_index("layer", append=True, inplace=True)
    geo_infos[-1].index.names = ["GADM_key", "GADM_layer"]

    geo_infos.append(gpd.read_file("../input_data/geodata_gadm/gadm_410-levels.zip", layer="ADM_1"))
    geo_infos[-1]["layer"] = 1
    geo_infos[-1].set_index("layer", append=True, inplace=True)
    geo_infos[-1].index.names = ["GADM_key", "GADM_layer"]

    geo_infos.append(gpd.read_file("../input_data/geodata_gadm/gadm_410-levels.zip", layer="ADM_2"))
    geo_infos[-1]["layer"] = 2
    geo_infos[-1].set_index("layer", append=True, inplace=True)
    geo_infos[-1].index.names = ["GADM_key", "GADM_layer"]

    geo_infos.append(gpd.read_file("../input_data/geodata_gadm/gadm_410-levels.zip", layer="ADM_3"))
    geo_infos[-1]["layer"] = 3
    geo_infos[-1].set_index("layer", append=True, inplace=True)
    geo_infos[-1].index.names = ["GADM_key", "GADM_layer"]

    agg1_gadm_levels_processed = {x: y for (x, y) in agg1_gadm_levels.items() if y != 1}
    agg2_gadm_levels_processed = {x: y for (x, y) in agg2_gadm_levels.items() if y != 2}

    philippines_2 = geo_infos[1][geo_infos[1]["COUNTRY"] == "Philippines"].rename(columns={
        "GID_1": "GID_2",
        "NAME_1": "NAME_2",
        "VARNAME_1": "VARNAME_2",
        "NL_NAME_1": "NL_NAME_2",
        "TYPE_1": "TYPE_2",
        "ENGTYPE_1": "ENGTYPE_2",
        "CC_1": "CC_2",
        "HASC_1": "HASC_2"
    })
    philippines_2["GID_1"] = philippines_2.loc[:, "GID_2"]
    philippines_2["NAME_1"] = philippines_2.loc[:, "NAME_2"]
    philippines_2["NL_NAME_1"] = philippines_2.loc[:, "NL_NAME_2"]

    new_geo_infos = [geo_infos[0],
                     pd.concat([geo_infos[1][~geo_infos[1]["COUNTRY"].isin(agg1_gadm_levels_processed.keys())],
                                geo_infos[2].drop(
                                  columns=["GID_1", "NAME_1", "NL_NAME_1"]
                                ).rename(columns={"GID_2": "GID_1",
                                                  "NAME_2": "NAME_1",
                                                  "VARNAME_2": "VARNAME_1",
                                                  "NL_NAME_2": "NL_NAME_1",
                                                  "TYPE_2": "TYPE_1",
                                                  "ENGTYPE_2": "ENGTYPE_1",
                                                  "CC_2": "CC_1",
                                                  "HASC_2": "HASC_1"}
                                         )[geo_infos[2]["COUNTRY"].isin(
                                  [k for k in agg1_gadm_levels_processed.keys() if agg1_gadm_levels_processed[k] == 2]
                                )]]),
                     pd.concat([philippines_2,
                                geo_infos[2][~geo_infos[2]["COUNTRY"].isin(agg2_gadm_levels_processed.keys())],
                                geo_infos[3].drop(
                                  columns=["GID_2", "NAME_2", "NL_NAME_2"]
                                ).rename(columns={"GID_3": "GID_2",
                                                  "NAME_3": "NAME_2",
                                                  "VARNAME_3": "VARNAME_2",
                                                  "NL_NAME_3": "NL_NAME_2",
                                                  "TYPE_3": "TYPE_2",
                                                  "ENGTYPE_3": "ENGTYPE_2",
                                                  "CC_3": "CC_2",
                                                  "HASC_3": "HASC_2"}
                                         )[geo_infos[3]["COUNTRY"].isin(
                                    [k for k in agg2_gadm_levels_processed.keys() if agg2_gadm_levels_processed[k] == 3]
                                )]])
                     ]

    new_geo_infos[0]["graph_node_index"] = np.arange(len(new_geo_infos[0]), dtype=np.int32)
    new_geo_infos[1]["graph_node_index"] = np.arange(len(new_geo_infos[1]), dtype=np.int32)
    new_geo_infos[2]["graph_node_index"] = np.arange(len(new_geo_infos[2]), dtype=np.int32)

    none_country_mask = [[],
                         list(filter(lambda k: agg1_gadm_levels_processed[k] is None,
                                     agg1_gadm_levels_processed.keys())),
                         list(filter(lambda k: agg2_gadm_levels_processed[k] is None,
                                     agg2_gadm_levels_processed.keys()))]

    def join_level(level, right_on):
        output_columns = (["location_key", "GADM_layer", "GADM_key", "graph_node_index", "country_name"]
                          + right_on + ["latitude", "longitude"])
        curr_locations_geo_and_index = locations_geo_and_index[
            locations_geo_and_index["aggregation_level"] == level].dropna(subset=["latitude", "longitude"])
        curr_locations_geo_and_index = curr_locations_geo_and_index[
            ~curr_locations_geo_and_index["country_name"].isin(none_country_mask[level])]
        curr_locations_geo_and_index_polars = pl.from_pandas(curr_locations_geo_and_index.drop(columns="geometry"))

        curr_geo = new_geo_infos[level]
        curr_geo_polars = pl.from_pandas(new_geo_infos[level].drop(columns="geometry"), include_index=True)

        match level:
            case 0:
                curr_geo_polars = curr_geo_polars.with_columns(
                    COUNTRY=pl.col("COUNTRY").replace(old=["México", "United States", "Czechia"],
                                                      new=["Mexico", "United States of America", "Czech Republic"])
                )
                name_joined = curr_locations_geo_and_index_polars.join(
                    curr_geo_polars, how="inner", left_on="iso_3166_1_alpha_3", right_on="GID_0", validate="1:1")[
                    output_columns].unique(subset="location_key", keep="none").unique(subset=["GADM_layer", "GADM_key"],
                                                                                  keep="none")
            case 1:
                curr_geo_polars = curr_geo_polars.with_columns(
                    COUNTRY=pl.col("COUNTRY").replace(old=["México", "United States", "Czechia"],
                                                      new=["Mexico", "United States of America", "Czech Republic"]),
                    NAME_1=pl.col("NAME_1").replace(
                        old=["Haut-Katanga", "Puntarenas", "Buenos Aires", "Matanzas", "Mayabeque", "Puerto Plata",
                             "Santo Domingo", "Gracias a Dios", "Islas de la Bahía", "Sulawesi Tengah",
                             "Andaman and Nicobar", "As-Sulaymaniyah", "Al Jabal al Gharbi", "An Nuqat al Khams",
                             "Misratah", "Al Jifarah", "Maputo", "Panamá", "Lima", "Lima Province",
                             "Khabarovsk", "Nenets"],
                        new=["Haut-Katanga Province", "Puntarenas Province", "Buenos Aires Province",
                             "Matanzas Province", "Mayabeque Province", "Puerto Plata Province",
                             "Santo Domingo Province", "Gracias a Dios Department", "Bay Islands Department",
                             "Central Sulawesi", "Andaman and Nicobar Islands", "Sulaymaniyah", "Jabal al Gharbi",
                             "Nuqat al Khams", "Misurata", "Al-Jafra", "Maputo Province", "Panamá Province",
                              "Lima Region", "Metropolitan Municipality of Lima", "Khabarovsk Krai",
                             "Nenets Avtonomnyy Okrug"])
                ).with_columns(
                    NAME_1=pl.when(
                        pl.col("GID_1").eq("GBR.1_1")
                    ).then(pl.lit("England")).when(
                        pl.col("GID_1").eq("HND.3_1")
                    ).then(pl.lit("Colón Department")).otherwise(pl.col("NAME_1"))
                )
                name_joined = curr_locations_geo_and_index_polars.join_where(
                    curr_geo_polars,
                    pl.col("iso_3166_1_alpha_3") == pl.col("GID_0"),
                    (pl.col("subregion1_name") == pl.col("NAME_1")) | pl.col("subregion1_name").is_in(
                    pl.col("VARNAME_1").replace("NA", None).str.split(by="|").fill_null(value=[]))
                )[output_columns].unique(subset="location_key", keep="none").unique(subset=["GADM_layer", "GADM_key"],
                                                                                    keep="none")
            case 2:
                curr_geo_polars = curr_geo_polars.join(
                    pl.from_pandas(new_geo_infos[1].drop(columns="geometry"), include_index=True),
                    how="left",
                    on="GID_1",
                    validate="m:1"
                ).lazy().with_columns(
                    COUNTRY=pl.col("COUNTRY").replace(old=["México", "United States", "Czechia"],
                                                      new=["Mexico", "United States of America", "Czech Republic"]),
                    NAME_1=pl.col("NAME_1").replace(
                        old=["Buenos Aires", "Ancash", "Santiago Metropolitan", "Niederösterreich",
                             "Nusa Tenggara Timur", "Jawa Tengah", "Jawa Timur", "Kalimantan Barat",
                             "Kalimantan Tengah", "Kalimantan Timur", "Maluku Utara", "Papua Barat",
                             "Sulawesi Barat", "Sulawesi Selatan", "Sulawesi Tengah", "Sulawesi Tenggara",
                             "Sumatera Barat", "Sumatera Selatan", "Sumatera Utara", "México", "Dolnośląskie",
                             "Zuid-Holland", "Noord-Brabant", "Kujawsko-Pomorskie", "Łódzkie", "Lubelskie", "Lubuskie",
                             "Małopolskie", "Mazowieckie", "Opolskie", "Podkarpackie", "Pomorskie", "Śląskie",
                             "Świętokrzyskie", "Warmińsko-Mazurskie", "Wielkopolskie", "Zachodniopomorskie", "Bío-Bío",
                             "Tirol", "Magallanes y Antártica Chilena", "Plzeňský", "Jihomoravský", "Bayern",
                             "Rheinland-Pfalz", "Sachsen", "Jawa Barat", "Jakarta Raya", "Kepulauan Riau", "Lima",
                             "Lima Province", "Nusa Tenggara Barat"],
                        new=["Buenos Aires Province", "Áncash", "Santiago Metropolitan Region", "Lower Austria",
                             "East Nusa Tenggara", "Central Java", "East Java", "West Kalimantan", "Central Kalimantan",
                             "East Kalimantan", "North Maluku", "West Papua", "West Sulawesi", "South Sulawesi",
                             "Central Sulawesi", "Southeast Sulawesi", "West Sumatra", "South Sumatra", "North Sumatra",
                             "State of Mexico", "Lower Silesia", "South Holland", "North Brabant", "Kuiavia-Pomerania",
                             "Łódź", "Lublin", "Lubusz", "Lesser Poland", "Mazovia", "Opole", "Subcarpathia",
                             "Pomerania", "Silesia", "Swietokrzyskie", "Warmia-Masuria", "Greater Poland",
                             "West Pomeranian", "Biobío", "Tyrol", "Magallanes", "Plzeň Region",
                             "South Moravian Region", "Bavaria", "Rhineland-Palatinate", "Saxony", "West Java",
                             "Jakarta", "Riau Islands", "Lima Region", "Metropolitan Municipality of Lima",
                             "West Nusa Tenggara"]),
                    NAME_2=pl.col("NAME_2").replace(
                        old=["Sankt Pölten Land", "Sankt Pölten Stadt", "Innsbruck Land", "Kutai Barat", "Viluppuram",
                             "San Andrés de Sotavento", "Nelson Mandela Bay", "Jose Crespo Y Castillo", "Brno",
                             "Brno-Venkov", "Plzeň - jih", "Plzeň - sever", "Plzeň", "Heilbronn (Stadtkreis)",
                             "Heilbronn", "Callaria", "Darjiling", "Innsbruck Stadt", "Balneário Piçarras",
                             "Vigía del Fuerte", "Palmar de Varela", "Rostock", "Rostock (Kreisfreie Stadt)", "Ansbach",
                             "Ansbach (Kreisfreie Stadt)", "Aschaffenburg", "Aschaffenburg (Kreisfreie Stadt)",
                             "Augsburg", "Augsburg (Kreisfreie Stadt)", "Bamberg", "Bamberg (Kreisfreie Stadt)",
                             "Bayreuth", "Bayreuth (Kreisfreie Stadt)", "La Unión de Isidoro Montes de Oc",
                             "Tlalixtaquilla de Maldonado", "Xalpatláhuac", "San Antonio la Isla", "Tenango del Valle",
                             "San Antonio Nanahuatípam", "Kepulauan Seribu", "Kaiserslautern (Kreisfreie Stadt",
                             "Nanchital de Lázaro Cárdenas del", "Tepetitla de Lardizábal", "Cohuecan",
                             "Santo Domingo Xagacía", "Huayllo", "Mariano Nicolas Valcarcel", "Caraveli", "Chancayba",
                             "Quimbiri", "Daniel Alomias Robles", "Hermilio Valdizan", "Puerto Bermudez",
                             "Łódzki Wschodni", "Częstochowa (CIty)", "Saint Louis", "Cacadu", "La Compañía", "Taniche",
                             "Villa Díaz Ordaz", "General Felipe Ángeles"],
                        new=["Sankt Pölten-Land", "Sankt Pölten", "Innsbruck-Land", "West Kutai", "Villupuram",
                             "San Andrés De Sotavento", "Nelson Mandela Bay Metropolitan Municipality",
                             "José Crespo y Castillo", "Brno-City District", "Brno-Country District",
                             "Plzeň-South District", "Plzeň-North District", "Plzeň-City District",
                             "Heilbronn Stadtkreis", "Landkreis Heilbronn", "Calleria", "Darjeeling", "Innsbruck-Stadt",
                             "Piçarras", "Vigía Del Fuerte", "Palmar De Varela", "Landkreis Rostock", "Rostock",
                             "Landkreis Ansbach", "Ansbach", "Landkreis Aschaffenburg", "Aschaffenburg",
                             "Landkreis Augsburg", "Augsburg", "Landkreis Bamberg", "Bamberg", "Landkreis Bayreuth",
                             "Bayreuth", "La Unión de Isidoro Montes de Oca", "Tlalixtaquilla", "Xalpatlahuac",
                             "San Antonio La Isla", "Tenango Del Valle", "San Antonio Nanahuatipam", "Thousand Islands",
                             "Kaiserslautern (Kreisfreie Stadt)", "Nanchital", "Tepetitla de Lardizabal", "Cohuecán",
                             "Santo Domingo Xagacia", "Ihuayllo", "Mariano Nicolás Valcárcel", "Caravelí",
                             "Chancaybaños", "Kimbiri", "Daniel Alomía Robles", "Hermílio Valdizan", "Puerto Bermúdez",
                             "Łódź East", "Częstochowa (City)", "St. Louis", "Sarah Baartman", "Q5962962", "Q20208810",
                             "Q27767632", "General Felipe Angeles"])
                ).with_columns(
                    NAME_2=pl.when(
                        pl.col("COUNTRY").eq("Peru"),
                        pl.col("NAME_1").eq("Amazonas"),
                        pl.col("NAME_2").eq("Asuncion")
                    ).then(pl.lit("Asunción")).when(
                        pl.col("COUNTRY").eq("Peru"),
                        pl.col("NAME_1").eq("Huancavelica"),
                        pl.col("NAME_2").eq("Mariscal Caceres")
                    ).then(pl.lit("Mariscal Cáceres")).when(
                        pl.col("COUNTRY").eq("Peru"),
                        pl.col("NAME_1").eq("Lima Region"),
                        pl.col("NAME_2").eq("Miraflores")
                    ).then(pl.lit("Miraflores, Yauyos")).when(
                        pl.col("COUNTRY").eq("Peru"),
                        pl.col("NAME_1").eq("Metropolitan Municipality of Lima"),
                        pl.col("NAME_2").eq("Miraflores")
                    ).then(pl.lit("Miraflores, Lima")).when(
                        pl.col("COUNTRY").eq("Peru"),
                        pl.col("NAME_1").eq("Lima Region"),
                        pl.col("NAME_2").eq("San Luis")
                    ).then(pl.lit("San Luis, Cañete")).when(
                        pl.col("COUNTRY").eq("Peru"),
                        pl.col("NAME_1").eq("Metropolitan Municipality of Lima"),
                        pl.col("NAME_2").eq("San Luis")
                    ).then(pl.lit("San Luis, Lima")).when(
                        pl.col("COUNTRY").eq("Poland"),
                        pl.col("ENGTYPE_2").eq("County")
                    ).then(pl.col("NAME_2") + " County").when(
                        pl.col("COUNTRY").eq("Poland"),
                        pl.col("ENGTYPE_2").eq("City with powiat rights")
                    ).then(pl.col("NAME_2").str.strip_suffix(" (City)")).when(
                        pl.col("COUNTRY").eq("Germany"),
                        pl.col("TYPE_2").eq("Landkreis")
                    ).then("Landkreis " + pl.col("NAME_2")).when(
                        pl.col("COUNTRY").eq("Germany"),
                        pl.col("TYPE_2").eq("Kreisfreie Stadt")
                    ).then(pl.col("NAME_2").str.strip_suffix(" (Kreisfreie Stadt)")).when(
                        pl.col("COUNTRY").eq("United States of America"),
                        pl.col("NAME_1").is_in(["Arkansas", "Florida", "Massachusetts", "Maryland", "Maine",
                                                "Michigan", "Missouri", "North Carolina", "New York", "Ohio",
                                                "Rhode Island", "South Carolina", "Texas", "Virginia", "Wisconsin"]),
                        pl.col("TYPE_2").eq("County")
                    ).then(pl.col("NAME_2") + " County").when(
                        pl.col("COUNTRY").eq("United States of America"),
                        pl.col("NAME_1").eq("Louisiana"),
                        pl.col("TYPE_2").eq("Parish")
                    ).then(pl.col("NAME_2") + " Parish").otherwise("NAME_2").replace(
                        old=["Landkreis Landkreis Heilbronn", "Landkreis Enzkreis", "Landkreis Darmstadt-Dieburg",
                             "Landkreis Südwestpfalz", "Zamość County"],
                        new=["Landkreis Heilbronn", "Enzkreis", "Darmstadt-Dieburg", "Südwestpfalz", "Zamość District"])
                )
                name_joined = curr_locations_geo_and_index_polars.lazy().with_columns(
                    subregion1_name_alt=pl.when(
                        pl.col("country_name").eq("Bangladesh"),
                                  pl.col("subregion1_name").eq("Khulna"),
                                  pl.col("subregion2_name").eq("Pabna") | pl.col("subregion2_name").eq("Natore")
                    ).then(pl.lit("Rajshahi")).otherwise(pl.col("subregion1_name"))
                ).join_where(
                    curr_geo_polars.with_columns(
                        alt_names1=pl.col("VARNAME_1").replace(
                            "NA", None).str.split(by="|").fill_null(value=[]),
                        alt_names2=pl.col("VARNAME_2").replace(
                            "NA", None).str.to_lowercase().str.split(by="|").fill_null(value=[])
                    ),
                    pl.col("iso_3166_1_alpha_3") == pl.col("GID_0"),
                    (pl.col("subregion1_name_alt") == pl.col("NAME_1")) | pl.col(
                        "subregion1_name_alt").is_in(pl.col("alt_names1")),
                    (pl.col("subregion2_name").str.to_lowercase() == pl.col("NAME_2").str.to_lowercase()) | pl.col(
                        "subregion2_name").str.to_lowercase().is_in(pl.col("alt_names2"))
                ).select(output_columns).unique(subset="location_key",
                                                keep="none").unique(subset=["GADM_layer", "GADM_key"],
                                                                    keep="none").collect(engine="streaming")
            case _:
                raise ValueError("This never should happen.")

        geo_joined = curr_geo[~curr_geo.index.isin(list(map(tuple, zip(name_joined.get_column("GADM_key").to_list(),
                                                                       name_joined.get_column("GADM_layer").to_list())))
                                                   )].sjoin(
            curr_locations_geo_and_index[
                ~curr_locations_geo_and_index["location_key"].isin(name_joined.get_column("location_key").to_list())],
            how="inner", predicate="contains")
        geo_joined = geo_joined[~geo_joined.index.duplicated(keep=False)].reset_index()[output_columns]

        pl.concat([name_joined, pl.from_pandas(geo_joined)]).with_columns(
            latitude=pl.col("latitude").cast(pl.Float32),
            longitude=pl.col("longitude").cast(pl.Float32)
        ).write_parquet("../intermediate_data/vertex_info/vertex_info_level_"+str(level)+".parquet",
                        compression="zstd",
                        compression_level=19)


    join_level(0, ["iso_3166_1_alpha_3"])
    join_level(1, ["iso_3166_1_alpha_3", "subregion1_name"])
    join_level(2, ["iso_3166_1_alpha_3", "subregion1_name", "subregion2_name"])
