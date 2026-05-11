agg1_gadm_levels = {'Afghanistan': 1,
                    'Argentina': 1,
                    'Austria': 1,
                    'Australia': 1,
                    'Bangladesh': 1,
                    'Belgium': 2,
                    'Bulgaria': 1,
                    'Bolivia': 1,
                    'Brazil': 1,
                    'Canada': 1,
                    'Democratic Republic of the Congo': 1,
                    'Switzerland': 1,
                    'Chile': 1,
                    'China': 1,
                    'Colombia': 1,
                    'Costa Rica': 1,
                    'Cuba': 1,
                    'Czech Republic': 1,
                    'Germany': 1,
                    'Dominican Republic': 1,
                    'Ecuador': 1,
                    'Estonia': 1,
                    'Spain': 1,
                    'France': 1,
                    'United Kingdom': 1,
                    'Guatemala': 1,
                    'Honduras': 1,
                    'Haiti': 1,
                    'Indonesia': 1,
                    'Israel': 1,
                    'India': 1,
                    'Iraq': 1,
                    'Italy': 1,
                    'Japan': 1,
                    'Kenya': 1,
                    'South Korea': 1,
                    'Libya': 1,
                    'Mexico': 1,
                    'Malaysia': 1,
                    'Mozambique': 1,
                    'Nicaragua': 1,
                    'Netherlands': 1,
                    'Norway': 1,
                    'Panama': 1,
                    'Peru': 1,
                    'Philippines': None,
                    'Pakistan': 1,
                    'Poland': 1,
                    'Portugal': None,
                    'Paraguay': 1,
                    'Romania': 1,
                    'Russia': 1,
                    'Sudan': 1,
                    'Sweden': 1,
                    'Slovenia': 1,
                    'Slovakia': 1,
                    'Sierra Leone': 1,
                    'El Salvador': 1,
                    'Thailand': 1,
                    'Taiwan': 2,
                    'Ukraine': 1,
                    'United States of America': 1,
                    'Uruguay': 1,
                    'Venezuela': 1,
                    'South Africa': 1}

agg2_gadm_levels = {'Argentina': 2,
                    'Austria': 2,
                    'Bangladesh': 2,
                    'Brazil': 2,
                    'Canada': None,
                    'Chile': 3,
                    'Colombia': 2,
                    'Czech Republic': 2,
                    'Germany': 2,
                    'Spain': None,
                    'France': 2,
                    'United Kingdom': 2,
                    'Indonesia': 2,
                    'Israel': None,
                    'India': 2,
                    'Italy': 2,
                    'Libya': None,
                    'Mexico': 2,
                    'Netherlands': 2,
                    'Peru': 3,
                    'Philippines': 1,
                    'Poland': 2,
                    'Sierra Leone': 2,
                    'United States of America': 2,
                    'South Africa': 2}

if __name__ == "__main__":
    from scipy.sparse import save_npz
    import torch
    import torch_geometric as tg
    import pandas as pd
    import geopandas as gpd

    agg1_gadm_levels = {x: y for (x, y) in agg1_gadm_levels.items() if y != 1}
    agg2_gadm_levels = {x: y for (x, y) in agg2_gadm_levels.items() if y != 2}

    geo_infos = [gpd.read_file("../input_data/geodata_gadm/gadm_410-levels.zip", layer="ADM_"+str(layer))
                 for layer in range(4)]
    for i in range(4):
      geo_infos[i]["layer"] = i
      geo_infos[i].set_index("layer", append=True, inplace=True)

    def create_featureless_full_graph(level: int):
        if level == 0:
          geo_info = geo_infos[0]
        elif level == 1 or level == 2:
          agg_to_gadm = agg1_gadm_levels if level == 1 else agg2_gadm_levels
          geo_info = pd.concat([geo_infos[level - 1][geo_infos[level - 1]["COUNTRY"].isin(
                                    [k for k in agg_to_gadm.keys() if agg_to_gadm[k] == level - 1])],
                                geo_infos[level][~geo_infos[level]["COUNTRY"].isin(agg_to_gadm.keys())],
                                geo_infos[level + 1][geo_infos[level + 1]["COUNTRY"].isin(
                                    [k for k in agg_to_gadm.keys() if agg_to_gadm[k] == level + 1])]])
        else:
          raise ValueError("'level' must be 0, 1 or 2")
        transforms = tg.transforms.Compose([tg.transforms.RemoveSelfLoops(),
                                            tg.transforms.RemoveDuplicatedEdges(),
                                            tg.transforms.ToUndirected()])
        big_graph = transforms(
          tg.data.Data(
            x=torch.arange(len(geo_info), dtype=torch.int32).unsqueeze(-1),
            edge_index=torch.as_tensor(
              geo_info['geometry'].sindex.query(geo_info['geometry'], predicate="intersects"),
              dtype=torch.int64)
          )
        ).coalesce()
        return tg.utils.to_scipy_sparse_matrix(edge_index=big_graph.edge_index,
                                               num_nodes=big_graph.num_nodes)


    save_npz("../intermediate_data/full_graphs/full_gadm_graph_level_0.npz",
             create_featureless_full_graph(0))

    save_npz("../intermediate_data/full_graphs/full_gadm_graph_level_1.npz",
             create_featureless_full_graph(1))

    save_npz("../intermediate_data/full_graphs/full_gadm_graph_level_2.npz",
             create_featureless_full_graph(2))
