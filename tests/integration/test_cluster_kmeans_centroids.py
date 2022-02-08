from relevanceai.http_client import Client, Dataset, ClusterOps


def test_dataset_api_kmeans_centroids_properties(test_client: Client, test_df: Dataset):

    alias: str = "test_alias"
    vector_field: str = "sample_1_vector_"

    from relevanceai.clusterer import KMeansModel

    print(test_df.shape)

    model = KMeansModel()

    clusterer: ClusterOps = test_client.ClusterOps(model=model, alias=alias)
    clusterer.fit_predict_update(dataset=test_df, vector_fields=[vector_field])

    assert f"_cluster_.{vector_field}.{alias}" in test_df.schema

    centroids = clusterer.centroids
    assert len(centroids) > 0
