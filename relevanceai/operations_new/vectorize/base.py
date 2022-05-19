from typing import List, Dict, Any

from abc import abstractmethod

from relevanceai.operations_new.vectorize.models.base import ModelBase
from relevanceai.operations_new.base import OperationsBase


class VectorizeBase(OperationsBase):

    models: List[ModelBase]
    fields: List[str]

    @abstractmethod
    def _get_model(self, *args, **kwargs):
        raise NotImplementedError

    def run(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """It takes a list of documents, and for each document, it runs the document through each of the
        models in the pipeline, and returns the updated documents.

        Parameters
        ----------
        documents : List[Dict[str, Any]]
            List[Dict[str, Any]]

        Returns
        -------
            A list of dictionaries.

        """

        updated_documents = documents

        for model in self.models:
            updated_documents = model.encode_documents(
                documents=updated_documents,
                fields=self.fields,
            )

        # removes unnecessary info for updated_where
        updated_documents = [
            {
                key: value
                for key, value in document.items()
                if key in self.fields or key == "_id"
            }
            for document in updated_documents
        ]

        return updated_documents