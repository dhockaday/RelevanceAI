import pytest

import random

from datetime import datetime

import uuid

import numpy as np
import pandas as pd


@pytest.fixture(scope="session")
def complex_nested_document():
    return {
        "_id": uuid.uuid4().__str__(),
        "sample_1": {
            "panda": pd.DataFrame(
                np.random.randint(0, 20, size=(20, 4)), columns=list("ABCD")
            ),
            "datetime": datetime.now(),
            "numpy": np.random.rand(3, 2),
            "test1": random.random(),
            "test2": random.random(),
        },
        "sample_2": {
            "subsample1": {
                "panda": pd.DataFrame(
                    np.random.randint(0, 20, size=(20, 4)), columns=list("ABCD")
                ),
                "datetime": datetime.now(),
                "numpy": np.random.rand(3, 2),
            },
            "subsample2": {
                "panda": pd.DataFrame(
                    np.array([[1, 2, np.nan], [4, np.nan, 6], [7, 8, 9]]),
                    columns=["a", "b", "c"],
                ),
                "datetime": datetime.now(),
                "numpy": np.random.rand(3, 2),
            },
        },
    }


@pytest.fixture(scope="session")
def simple_nested_document():
    return {
        "_id": uuid.uuid4.__str__(),
        "col1": {"subcol1": random.random(), "subcol2": random.random()},
        "col2": {"subcol3": random.random(), "subcol4": random.random()},
        "col3": {"subcol5": random.random(), "subcol6": random.random()},
        "col4": {"subcol7": random.random(), "subcol8": random.random()},
    }
