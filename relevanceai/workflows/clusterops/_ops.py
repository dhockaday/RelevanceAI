import os
import json
import getpass

import numpy as np

from doc_utils import DocUtils
from doc_utils.read_utils import DocReadUtils

from typing import Union, Optional, Callable, List, Dict, Any
from relevanceai.api.client import BatchAPIClient
from relevanceai.package_utils.base import _Base

from relevanceai.package_utils.integration_checks import (
    is_sklearn_available,
    is_hdbscan_available,
)

from relevanceai.dataset_interface import Dataset
from relevanceai.workflows.clusterops.cluster_base import (
    CentroidClusterBase,
    BatchClusterBase,
    SklearnCentroidBase,
    HDBSCANClusterBase,
    ClusterBase,
)


class _ClusterOps(BatchAPIClient):

    model: Union[BatchClusterBase, ClusterBase, CentroidClusterBase]
    dataset_id: str
    vector_fields: List[Any]
    cluster_field: str
    parent_alias: Optional[str]

    # Adding first-class sklearn integration
    def _assign_sklearn_model(self, model):
        # Add support for not just sklearn models but sklearn models
        # with first -class integration for kmeans
        from sklearn.cluster import (
            KMeans,
            MiniBatchKMeans,
            DBSCAN,
            Birch,
            SpectralClustering,
            OPTICS,
            AgglomerativeClustering,
            AffinityPropagation,
            MeanShift,
            FeatureAgglomeration,
        )

        POSSIBLE_MODELS = [
            SpectralClustering,
            Birch,
            DBSCAN,
            OPTICS,
            AgglomerativeClustering,
            AffinityPropagation,
            MeanShift,
            FeatureAgglomeration,
        ]
        if is_hdbscan_available():
            import hdbscan

            if hasattr(hdbscan, "HDBSCAN"):
                POSSIBLE_MODELS.append(hdbscan.HDBSCAN)
        if model.__class__ == KMeans:

            class CentroidClusterModel(CentroidClusterBase):
                def __init__(self, model):
                    self.model: Union[KMeans, MiniBatchKMeans] = model

                def fit_predict(self, X):
                    return self.model.fit_predict(X)

                def get_centers(self):
                    return self.model.cluster_centers_

            new_model = CentroidClusterModel(model)
            return new_model

        elif model.__class__ == MiniBatchKMeans:

            class BatchCentroidClusterModel(CentroidClusterBase, BatchClusterBase):
                def __init__(self, model):
                    self.model: MiniBatchKMeans = model

                def partial_fit(self, X):
                    return self.model.partial_fit(X)

                def predict(self, X):
                    return self.model.predict(X)

                def get_centers(self):
                    return self.model.cluster_centers_

            new_model = BatchCentroidClusterModel(model)
            return new_model

        elif isinstance(model, tuple(POSSIBLE_MODELS)):
            # new_model = CentroidClusterModel(model)
            if "sklearn" in str(type(model)).lower():
                new_model = SklearnCentroidBase(model)
            elif "hdbscan" in str(type(model)).lower():
                new_model = HDBSCANClusterBase(model)
            return new_model
        elif hasattr(model, "fit_documents"):
            return model
        elif hasattr(model, "fit_predict"):
            data = {"fit_predict": model.fit_predict, "metadata": model.__dict__}
            ClusterModel = type("ClusterBase", (ClusterBase,), data)
            return ClusterModel()
        elif hasattr(model, "fit_transform"):
            data = {"fit_predict": model.fit_transform, "metadata": model.__dict__}
            ClusterModel = type("ClusterBase", (ClusterBase,), data)
            return ClusterModel()

    def _assign_model(self, model):
        # Check if this is a model that will fit
        # otherwise - forces a Clusterbase
        if (is_sklearn_available() or is_hdbscan_available()) and (
            "sklearn" in str(type(model)).lower()
            or "hdbscan" in str(type(model)).lower()
        ):
            model = self._assign_sklearn_model(model)
            if model is not None:
                return model

        if isinstance(model, ClusterBase):
            return model
        elif hasattr(model, "fit_documents"):
            return model
        # elif hasattr(model, "fit_predict"):
        #     # Support for SKLEARN interface
        #     data = {"fit_predict": model.fit_predict, "metadata": model.__dict__}
        #     ClusterModel = type("ClusterBase", (ClusterBase,), data)
        #     return ClusterModel()
        elif hasattr(model, "fit_predict"):
            data = {"fit_predict": model.fit_predict, "metadata": model.__dict__}
            ClusterModel = type("ClusterBase", (ClusterBase,), data)
            return ClusterModel()
        elif model is None:
            return model
        raise TypeError("Model should be inherited from ClusterBase.")

    def _token_to_auth(self, token=None):
        SIGNUP_URL = "https://cloud.relevance.ai/sdk/api"

        if os.path.exists(self._cred_fn):
            credentials = self._read_credentials()
            return credentials

        elif token:
            return self._process_token(token)

        else:
            print(f"Activation token (you can find it here: {SIGNUP_URL} )")
            if not token:
                token = getpass.getpass(f"Activation token:")
            return self._process_token(token)

    def _process_token(self, token: str):
        split_token = token.split(":")
        project = split_token[0]
        api_key = split_token[1]
        if len(split_token) > 2:
            region = split_token[3]
            base_url = self._region_to_url(region)

            if len(split_token) > 3:
                firebase_uid = split_token[4]
                return self._write_credentials(
                    project=project,
                    api_key=api_key,
                    base_url=base_url,
                    firebase_uid=firebase_uid,
                )

            else:
                return self._write_credentials(
                    project=project, api_key=api_key, base_url=base_url
                )

        else:
            return self._write_credentials(project=project, api_key=api_key)

    def _read_credentials(self):
        return json.load(open(self._cred_fn))

    def _write_credentials(self, **kwargs):
        print(
            f"Saving credentials to {self._cred_fn}. Remember to delete this file if you do not want credentials saved."
        )
        json.dump(
            kwargs,
            open(self._cred_fn, "w"),
        )
        return kwargs

    def _init_dataset(self, dataset):
        # set dataset ID and dataset attributes for consistent usage
        if isinstance(dataset, Dataset):
            self.dataset_id = dataset.dataset_id
            self.dataset: Dataset = dataset
        elif isinstance(dataset, str):
            self.dataset_id = dataset
            self.dataset = Dataset(
                project=self.project,
                api_key=self.api_key,
                dataset_id=self.dataset_id,
                firebase_uid=self.firebase_uid,
            )
        else:
            raise ValueError(
                "Dataset type needs to be either a string or Dataset instance."
            )

    def _insert_centroid_documents(self):
        if hasattr(self.model, "get_centroid_documents"):
            print("Inserting centroid documents...")
            centers = self.get_centroid_documents()

            # Change centroids insertion
            results = self.services.cluster.centroids.insert(
                dataset_id=self.dataset_id,
                cluster_centers=centers,
                vector_fields=self.vector_fields,
                alias=self.alias,
            )
            self.logger.info(results)

        return

    def _check_dataset_id(self, dataset: Optional[Union[str, Dataset]] = None) -> str:
        """Helper method to get multiple dataset values"""

        if isinstance(dataset, Dataset):
            dataset_id: str = dataset.dataset_id
        elif isinstance(dataset, str):
            dataset_id = dataset
        elif dataset is None:
            if hasattr(self, "dataset_id"):
                # let's not surprise users
                print(
                    f"No dataset supplied - using last stored one '{self.dataset_id}'."
                )
                dataset_id = str(self.dataset_id)
            else:
                raise ValueError("Please supply dataset.")
        return dataset_id

    def _fit(
        self,
        vector_fields: List[Any],
        documents: List[Dict],
        return_only_clusters: bool = True,
        inplace: bool = True,
        include_report: bool = False,
    ):
        """
        Train clustering algorithm on documents and then store the labels
        inside the documents.

        Parameters
        -----------
        vector_field: list
            The vector field of the documents
        docs: list
            List of documents to run clustering on
        alias: str
            What the clusters can be called
        cluster_field: str
            What the cluster fields should be called
        return_only_clusters: bool
            If True, return only clusters, otherwise returns the original document
        inplace: bool
            If True, the documents are edited inplace otherwise, a copy is made first
        kwargs: dict
            Any other keyword argument will go directly into the clustering algorithm

        Example
        -----------

        .. code-block::

            from relevanceai import Client
            client = Client()
            df = client.Dataset("sample_dataset")

            from sklearn.cluster import MiniBatchKMeans
            model = MiniBatchKMeans(n_clusters=2)
            cluster_ops = client.ClusterOps(alias="minibatchkmeans_2", model=model)

            cluster_ops.fit_predict_documents(df, vector_fields=["documentation_vector_"])

        """
        self.vector_fields = vector_fields

        vectors = self._get_vectors_from_documents(vector_fields, documents)

        cluster_labels = self.model.fit_predict(vectors)

        if not self.parent_alias:
            cluster_labels_values = self._label_clusters(cluster_labels)
        else:
            prev_cluster_labels = self._get_parent_cluster_values(
                vector_fields=vector_fields,
                alias=self.parent_alias,
                documents=documents,
            )
            cluster_labels_values = self._label_subclusters(
                labels=cluster_labels, prev_cluster_labels=prev_cluster_labels
            )

        if include_report:
            try:
                self._calculate_silhouette_grade(vectors, cluster_labels_values)
            except Exception as e:
                print(e)
                pass
        return self.set_cluster_labels_across_documents(
            cluster_labels=cluster_labels_values,
            documents=documents,
            inplace=inplace,
            return_only_clusters=return_only_clusters,
        )

    def _get_parent_cluster_values(
        self, vector_fields: List[Any], alias: str, documents
    ) -> list:
        field = ".".join([self.cluster_field, ".".join(sorted(vector_fields)), alias])
        return self.get_field_across_documents(
            field, documents, missing_treatment="skip"
        )

    @staticmethod
    def _calculate_silhouette_grade(vectors, cluster_labels):
        from relevanceai.reports.cluster_report.grading import get_silhouette_grade
        from sklearn.metrics import silhouette_samples

        score = silhouette_samples(vectors, cluster_labels, metric="euclidean").mean()
        grade = get_silhouette_grade(score)

        print("---------------------------")
        print(f"Grade: {grade}")
        print(f"Mean Silhouette Score: {score}")
        print("---------------------------")

    def set_cluster_labels_across_documents(
        self,
        cluster_labels: list,
        documents: List[Dict],
        inplace: bool = True,
        return_only_clusters: bool = True,
    ):
        """
        Utility function to allow users to set cluster labels

        Parameters
        ------------
        cluster_labels: List[str, int]
            A list of integers of string. If it is an integer - it will automatically add a 'cluster-' prefix
            to help avoid incorrect data type parsing. You can override this behavior by setting clusters
            as strings.
        documents: List[dict]
            When the documents are in
        inplace: bool
            If True, then the clusters are set in place.
        return_only_clusters: bool
            If True, then the return_only_clusters will return documents with just the cluster field and ID.
            This can be helpful when you want to upsert quickly without having to re-insert the entire document.

        Example
        -----------

        .. code-block::

            labels = list(range(10))
            documents = [{"_id": str(x)} for x in range(10)]
            cluster_ops.set_cluster_labels_across_documents(labels, documents)

        """
        if inplace:
            self._set_cluster_labels_across_documents(cluster_labels, documents)
            if return_only_clusters:
                return [
                    {"_id": d.get("_id"), self.cluster_field: d.get(self.cluster_field)}
                    for d in documents
                ]
            return documents

        # useful if you want to upload as quickly as possible
        new_documents = documents.copy()

        self._set_cluster_labels_across_documents(cluster_labels, new_documents)
        if return_only_clusters:
            return [
                {"_id": d.get("_id"), self.cluster_field: d.get(self.cluster_field)}
                for d in new_documents
            ]
        return new_documents

    def _get_cluster_field_name(self, alias: str = None):
        if alias is None:
            alias = self.alias
        if isinstance(self.vector_fields, list):
            set_cluster_field = (
                f"{self.cluster_field}.{'.'.join(self.vector_fields)}.{alias}"
            )
        elif isinstance(self.vector_fields, str):
            set_cluster_field = f"{self.cluster_field}.{self.vector_fields}.{alias}"
        return set_cluster_field

    def _set_cluster_labels_across_documents(self, cluster_labels, documents):
        set_cluster_field = self._get_cluster_field_name()
        self.set_field_across_documents(set_cluster_field, cluster_labels, documents)

    def _label_cluster(self, label: Union[int, str]):
        if not isinstance(label, str):
            return "cluster-" + str(label)
        return str(label)

    def _label_subcluster(self, label: Union[int, str], prev_cluster_label) -> str:
        return prev_cluster_label + "-" + str(label)

    def _label_clusters(self, labels):
        return [self._label_cluster(x) for x in labels]

    def _label_subclusters(self, labels: List[str], prev_cluster_labels: List[str]):
        return [
            self._label_subcluster(label, prev_cluster_label)
            for label, prev_cluster_label in zip(labels, prev_cluster_labels)
        ]

    def _chunk_dataset(
        self,
        select_fields: Optional[list] = None,
        chunksize: int = 100,
        filters: Optional[list] = None,
    ):
        """Utility function for chunking a dataset"""
        select_fields = [] if select_fields is None else select_fields
        filters = [] if filters is None else filters

        docs = self._get_documents(
            dataset_id=self.dataset.dataset_id,
            include_cursor=True,
            number_of_documents=chunksize,
            select_fields=select_fields,
            filters=filters,
        )

        while len(docs["documents"]) > 0:
            yield docs["documents"]
            docs = self._get_documents(
                dataset_id=self.dataset.dataset_id,
                cursor=docs["cursor"],
                include_cursor=True,
                select_fields=select_fields,
                number_of_documents=chunksize,
                filters=filters,
            )

    def _check_for_dataset_id(self):
        if not hasattr(self, "dataset_id"):
            raise ValueError(
                "You are missing a dataset ID. Please set using the argument dataset_id='...'."
            )

    def _concat_vectors_from_list(self, list_of_vectors: list):
        """Concatenate 2 vectors together in a pairwise fashion"""
        return [np.concatenate(x) for x in list_of_vectors]

    def _get_vectors_from_documents(self, vector_fields: list, documents: List[Dict]):
        if len(vector_fields) == 1:
            # filtering out entries not containing the specified vector
            documents = list(filter(DocUtils.list_doc_fields, documents))
            vectors = self.get_field_across_documents(
                vector_fields[0], documents, missing_treatment="skip"
            )
        else:
            # In multifield clusering, we get all the vectors in each document
            # (skip if they are missing any of the vectors)
            # Then run clustering on the result
            documents = list(self.filter_docs_for_fields(vector_fields, documents))
            all_vectors = self.get_fields_across_documents(
                vector_fields, documents, missing_treatment="skip_if_any_missing"
            )
            # Store the vector field lengths to de-concatenate them later
            self._vector_field_length: dict = {}
            prev_vf = 0
            for i, vf in enumerate(self.vector_fields):
                self._vector_field_length[vf] = {}
                self._vector_field_length[vf]["start"] = prev_vf
                end_vf = prev_vf + len(all_vectors[0][i])
                self._vector_field_length[vf]["end"] = end_vf
                # Update the ending
                prev_vf = end_vf

            # Store the vector lengths
            vectors = self._concat_vectors_from_list(all_vectors)

        return vectors

    def _operate(self, cluster_id: str, field: str, output: dict, func: Callable):
        """
        Internal function for operations
        """
        cluster_field = self._get_cluster_field_name()
        # TODO; change this to fetch all documents
        documents = self.datasets.documents.get_where(
            self.dataset_id,
            filters=[
                {
                    "field": cluster_field,
                    "filter_type": "exact_match",
                    "condition": "==",
                    "condition_value": cluster_id,
                },
                {
                    "field": field,
                    "filter_type": "exists",
                    "condition": ">=",
                    "condition_value": " ",
                },
            ],
            select_fields=[field, cluster_field],
            page_size=9999,
        )
        # get the field across each
        arr = self.get_field_across_documents(field, documents["documents"])
        output[cluster_id] = func(arr)

    def _get_filter_for_cluster(self, cluster_id):
        cluster_field = self._get_cluster_field_name()
        filters = [
            {
                "field": cluster_field,
                "filter_type": "exact_match",
                "condition": "==",
                "condition_value": cluster_id,
            }
        ]
        return filters
