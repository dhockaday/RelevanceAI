import pytest

from typing import Dict, List

from tests.globals.utils import NUMBER_OF_DOCUMENTS


@pytest.fixture(scope="session")
def dataclass_documents(dataclass_document: Dict) -> List:
    return [dataclass_document for _ in range(NUMBER_OF_DOCUMENTS)]
