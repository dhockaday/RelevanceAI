"""
Datasets to mock
"""

from typing import List, Union
import sys
import pandas as pd
import requests

THIS_MODULE = sys.modules[__name__]
DATASETS = ['games', 'dummy_ecommerce', 'sample_ecommerce', 'online_retail', 'news', 'ecommerce', 'flipkart', 'realestate']

class SampleDatasets:
    def __init__(self):
        self.datasets = DATASETS

    def list_datasets(self):
        return self.datasets
        
    def get_dataset(self, name, *args, **kwargs):
        if name in self.datasets:
            return getattr(THIS_MODULE,f'get_{name}_dataset')(*args, **kwargs)
        else:
            raise ValueError('Not a valid dataset')

    @staticmethod
    def _get_dummy_dataset(db_name, number_of_documents, select_fields = []):
        from .http_client import Client
        project = "dummy-collections"
        api_key = (
            "UzdYRktIY0JxNmlvb1NpOFNsenU6VGdTU0s4UjhUR0NsaDdnQTVwUkpKZw"  # read access
        )
        client = Client(
            project,
            api_key,
        )
        response = client.datasets.documents.get_where(
            db_name,
            page_size=number_of_documents,
            select_fields = select_fields
        )
        if "message" in response:
            import warnings
            warnings.warn(response["message"])
        docs = response["documents"]
        return docs

    @staticmethod
    def _get_online_dataset(url, number_of_documents, drop_columns = [], encoding = None, csv = True):
        if csv:
            data = pd.read_csv(url, encoding=encoding).drop(columns = drop_columns).to_dict(orient="records")
        else:
            data = pd.read_excel(url).drop(columns = drop_columns).to_dict(orient="records")
        if number_of_documents:
            data = data[:number_of_documents]
        return data

    @staticmethod
    def _get_api_dataset(url, number_of_documents):
        data = requests.get(url).json()
        if number_of_documents:
            data = data[:number_of_documents]
        return data


def get_games_dataset(number_of_documents: Union[None, int] = 365) -> List:
    """Function to download a sample games dataset.
    Dataset from https://www.freetogame.com/
    Total Len: 365
    Sample document:
    {'id': 1,
    'title': 'Dauntless',
    'thumbnail': 'https://www.freetogame.com/g/1/thumbnail.jpg',
    'short_description': 'A free-to-play, co-op action RPG with gameplay similar to Monster Hunter.',
    'game_url': 'https://www.freetogame.com/open/dauntless',
    'genre': 'MMORPG',
    'platform': 'PC (Windows)',
    'publisher': 'Phoenix Labs',
    'developer': 'Phoenix Labs, Iron Galaxy',
    'release_date': '2019-05-21',
    'freetogame_profile_url': 'https://www.freetogame.com/dauntless'
    }
    """
    return SampleDatasets._get_api_dataset("https://www.freetogame.com/api/games", number_of_documents)


def get_dummy_ecommerce_dataset(
    db_name: str = "ecommerce-5",
    count: int = 1000
):
    """Here, we get the e-commerce dataset."""
    return SampleDatasets._get_dummy_dataset(db_name, count)



def get_sample_ecommerce_dataset(
    number_of_documents: int = 1000, select_fields: list = ["product_image", "product_title", "product_description", "product_image_clip_vector_"]
):
    docs = SampleDatasets._get_dummy_dataset("quickstart_data_sample", number_of_documents, select_fields)
    for d in docs:
        if "image_first" in d:
            d["image"] = d.pop("image_first")
    return docs


def get_online_retail_dataset(number_of_documents: Union[None, int] = 1000) -> List:
    """Online retail dataset from UCI machine learning
    Total Len: 406829
    Sample document:
    {'Country': 'United Kingdom',
    'CustomerID': 17850.0,
    'Description': 'WHITE HANGING HEART T-LIGHT HOLDER',
    'InvoiceDate': Timestamp('2010-12-01 08:26:00'),
    'InvoiceNo': 536365,
    'Quantity': 6,
    'StockCode': '85123A',
    'UnitPrice': 2.55}

    """
    return SampleDatasets._get_online_dataset("https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx", number_of_documents, csv = False)

def get_news_dataset(number_of_documents: Union[None, int] = 250) -> List:
    """News dataset
    Total Len: 250
    Sample document:
    {'Unnamed: 0': 0,
    'authors': 'Ruth Harris',
    'content': 'Sometimes the power of Christmas will make you do wild and wonderful things. You do not need to believe in the Holy Trinity to believe in the positive power of doing good for others. The simple act of giving without receiving is lost on many of us these days, as worries about money and success hold us back from giving to others who are in need. One congregation in Ohio was moved to action by the power of a sermon given at their church on Christmas Eve. The pastor at Grand Lake United Methodist Church in Celina, Ohio gave an emotional sermon about the importance of understanding the message of Jesus.\n\nFor many religious people the message of Jesus is to help others before yourself, to make sure the people who are suffering get the help they need to enjoy life a little bit. The sermon was really about generosity and what that can look like in our lives. Jesus lived a long time ago and he acted generously in the fashion of his time – but what would a generous act look like in our times? That was the focus of the sermon.\n\nThe potency of the sermon was not lost on the congregation, who were so moved they had to take action! After the sermon ended, the congregation decided to take an offering. A bowl was passed around the room and everyone pitched in what they could on this Christmas Eve with the words of the sermon still ringing in their ears.\n\nWhat did they do with this offering? Members of the congregation drove down to the local Waffle House to visit the ladies working the night shift. What a great choice on this most holy of days when everyone should be with their families!\n\nThe ladies working at Waffle House clearly were not with their families. They had no choice but to work on this holy day because it paid the bills. The congregation understood the sacrifice being made by these ladies, and wanted to help them out. They donated the entire offering to be split amongst the ladies at Waffle House.\n\nIn total that amounted to $3,500 being split amongst the staff. What a beautiful moment! What a perfect example of what the preacher was talking about in his sermon! Doing a good deed like this on Christmas really helped ease the burden felt by the ladies working at Waffle House. Sure, they could not see their families, but at least they got a little gift from the good people of their community.\n\nPerhaps the best part about this whole event was that the congregation did not ask anything in return. It was a simple act of generosity from people who understood the pain being felt by another group and sought to alleviate some of that pain. It speaks volumes about the merits of the Church in our daily lives. This simple act brought the entire community together because it showed empathy and compassion on the most special day of the year.',
    'domain': 'awm.com',
    'id': 141,
    'inserted_at': '2018-02-02 01:19:41.756632',
    'keywords': nan,
    'meta_description': nan,
    'meta_keywords': "['']",
    'scraped_at': '2018-01-25 16:17:44.789555',
    'summary': nan,
    'tags': nan,
    'title': 'Church Congregation Brings Gift to Waitresses Working on Christmas Eve, Has Them Crying (video)',
    'type': 'unreliable',
    'updated_at': '2018-02-02 01:19:41.756664',
    'url': 'http://awm.com/church-congregation-brings-gift-to-waitresses-working-on-christmas-eve-has-them-crying-video/'}
    """
    return SampleDatasets._get_online_dataset("https://raw.githubusercontent.com/several27/FakeNewsCorpus/master/news_sample.csv", number_of_documents, drop_columns=['Unnamed: 0'])

def get_ecommerce_dataset(number_of_documents: Union[None, int] = 1000) -> List:
    """Function to download a sample ecommerce dataset
    Dataset from https://data.world/crowdflower/ecommerce-search-relevance
    Total Len: 15528
    Sample document:
    {'_unit_id': 711158459,
    'product_description': 'The PlayStation 4 system opens the door to an '
                        'incredible journey through immersive new gaming '
                        'worlds and a deeply connected gaming community. Step '
                        'into living, breathing worlds where you are hero of '
                        '...',
    'product_image': 'http://thumbs2.ebaystatic.com/d/l225/m/mzvzEUIknaQclZ801YCY1ew.jpg',
    'product_link': 'http://www.ebay.com/itm/Sony-PlayStation-4-PS4-Latest-Model-500-GB-Jet-Black-Console-/321459436277?pt=LH_DefaultDomain_0&hash=item4ad879baf5',
    'product_price': '$329.98 ',
    'product_title': 'Sony PlayStation 4 (PS4) (Latest Model)- 500 GB Jet Black '
                    'Console',
    'query': 'playstation 4',
    'rank': 1,
    'relevance': 3.67,
    'relevance:variance': 0.471,
    'source': 'eBay',
    'url': 'http://www.ebay.com/sch/i.html?_from=R40&_trksid=p2050601.m570.l1313.TR11.TRC1.A0.H0.Xplant.TRS0&_nkw=playstation%204'}
    """

    df = SampleDatasets._get_online_dataset("https://query.data.world/s/glc7oe2ssd252scha53mu7dy2e7cft", number_of_documents, encoding = "ISO-8859-1")
    df = pd.DataFrame(df)
    df["product_image"] = df["product_image"].str.replace("http://", "https://")
    df["product_link"] = df["product_link"].str.replace("http://", "https://")
    df["url"] = df["url"].str.replace("http://", "https://")
    df["_id"] = df["_unit_id"].astype(str)
    return df.to_dict("records")


def get_flipkart_dataset(number_of_documents: Union[None, int] = 20000) -> List:
    """Function to download the flipkat ecommerce dataset
    Sample document in this dataset:
    {'Unnamed: 0': 0,
    '_id': 0,
    'product_name': "Alisha Solid Women's Cycling Shorts",
    'description': "Key Features of Alisha Solid Women's Cycling Shorts Cotton Lycra Navy, Red, Navy,Specifications of Alisha Solid Women's Cycling Shorts Shorts Details Number of Contents in Sales Package Pack of 3 Fabric Cotton Lycra Type Cycling Shorts General Details Pattern Solid Ideal For Women's Fabric Care Gentle Machine Wash in Lukewarm Water, Do Not Bleach Additional Details Style Code ALTHT_3P_21 In the Box 3 shorts",
    'retail_price': 999.0}
    """
    return SampleDatasets._get_online_dataset("https://raw.githubusercontent.com/arditoibryan/Projects/master/20211108_flipkart_df/flipkart.csv", number_of_documents, drop_columns=['Unnamed: 0'])

def get_realestate_dataset(
    number_of_documents: int = 50,
    filters = []
):
    return SampleDatasets._get_dummy_dataset('realestate', number_of_documents, filters)

def get_mission_statements_dataset(
    number_of_documents: Union[None, int] = 1433
) -> List:
    """Function to download a sample company mission statement dataset.
    Total Len: 1433
    Sample document:
    {'_id': 0,
    'company': 'Starbucks',
    'text': 'Establish Starbucks as the premier purveyor of the finest coffee in the world while maintaining our uncompromising principles while we grow.'},
    """
    df = pd.read_csv(
        "https://raw.githubusercontent.com/arditoibryan/Projects/master/20211111_company_statements/companies_preprocessed.csv"
    ).drop(["Unnamed: 0"], axis=1)
    df = df.reset_index(drop=False)
    df.columns = ["_id", "company", "text"]
    if number_of_documents:
        df = df[:number_of_documents]
    df = df.to_dict(orient="records")
    return df


def get_machine_learning_research_dataset():
    """Here we get our Machine Learning research dataset."""
    raise NotImplementedError
