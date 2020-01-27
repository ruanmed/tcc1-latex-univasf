import time
import math
import subprocess
from arango import ArangoClient
from elasticsearch import Elasticsearch
from elasticsearch import helpers as ElasticsearchHelpers
import xml.etree.ElementTree as ET
import pandas as pd
import json
from shlex import quote
...
class IndexToolManager:
    '''
    A class used to manage the database indexation tools used in this research.
    Provides functions to index a database with ArangoDB, Elasticsearch and Zettair,
    using the BM25 IR function implemented in each of those tools.
    Also makes it possible to query the indexed database using BM25.

    Attributes
    ----------
    indexName : str
        a string to refer to the current working data set

    bm25_b : float
        BM25 b parameter to adjust the document length compensation

    bm25_k1 : float
        BM25 k1 parameter to adjust the term-frequency weight

    bm25_k3 : float
        BM25 k3 parameter to adjust the term-frequency weight in the query (used for long queries)

    top_k : int
        Number of results to be retrieved when querying the database

    '''

    def __init__(self, indexName='default_index',
                 bm25_b=0.75, bm25_k1=1.2, bm25_k3=0.0, top_k=100):
        self.indexName = indexName
        self.bm25_b = float(bm25_b)
        self.bm25_k1 = float(bm25_k1)
        self.bm25_k3 = float(bm25_k3)
        self.numberResults = int(top_k)
        self.root_path = "/home/ruan/Documentos/git/tcc-ii-ir-features-text-mining/tool-testing/"

        self.zettair_query_process = None

        self.initializeArango()
        self.initializeElastic()

        self.resultsIndexName = 'tcc_results'
        body = {
            "settings": {
                "number_of_shards": 1,
            }
        }
        if not self.elasticClient.indices.exists(index=self.resultsIndexName):
            self.elasticClient.indices.create(
                index=self.resultsIndexName, body=body)

        # Create a new database named "resultsIndexName" if it does not exist.
        if not self.arango_sys_db .has_database(self.resultsIndexName):
            self.arango_sys_db .create_database(self.resultsIndexName)

        # Connect to "resultsIndexName" database as root user.
        # This returns an API wrapper for "resultsIndexName" database.
        self.arangoResultsDb = self.arangoClient.db(
            self.resultsIndexName, username=None, password=None)

        db = self.arangoResultsDb
        # Create a new collection named "resultsIndexName" if it does not exist.
        # This returns an API wrapper for "resultsIndexName" collection.
        if db.has_collection(self.resultsIndexName):
            self.arangoResultsCollection = db.collection(self.resultsIndexName)
        else:
            self.arangoResultsCollection = db.create_collection(
                self.resultsIndexName)

    ...

    def log_result(self, itemKey, itemBody):
        '''
        Inserts a document in the Elasticsearch database.

        Parameters
        ----------
        itemKey : str or number
            Document identifier

        itemBody : dict
            Document body/data.
        '''

        self.elasticClient.index(
            index=self.resultsIndexName, doc_type=self.elasticDocumentType,
            id=itemKey, body=itemBody)

        document = {'_key': itemKey}
        document.update(itemBody)
        self.arangoResultsCollection.insert(document)
    
    ...

    def get_documents(self, db='authorprof',
                      documents_xml_folder='db_authorprof/en/',
                      truth_txt='db_authorprof/truth.txt',
                      append_class_to_id=False):
        '''
        Generates a list with all documents from db formatted files.

        Parameters
        ----------
        db : str
            Database name.

        documents_xml_folder : str
            Folder that contains the XML files from the authors' documents (twits),
            must follow the DB_AUTHORPROF task XML format.

        truth_txt : str
            Truth TXT file with authors' classifications of gender { female | male },
            must follow the DB_AUTHORPROF task TXT format.
        '''
        if (db == 'authorprof'):
            return self.get_documents_DB_AUTHORPROF(documents_xml_folder, truth_txt, append_class_to_id)
        if (db == 'botgender'):
            return self.get_documents_DB_BOTGENDER(documents_xml_folder, truth_txt, append_class_to_id)
        if (db == 'hyperpartisan'):
            return self.get_documents_DB_HYPERPARTISAN(documents_xml_folder, truth_txt, append_class_to_id)
        if (db == 'hyperpartisan_split_42'):
            return self.get_documents_DB_HYPERPARTISAN_split(documents_xml_folder, truth_txt, append_class_to_id)

        return []
    ...

    def calc_IR(self, result_df, positive_class='true'):
        '''
        Calculates IR attributes suggested in the research:
            CLASS_0_BM25_AVG
            CLASS_0_BM25_COUNT
            CLASS_0_BM25_SUM
            CLASS_1_BM25_AVG
            CLASS_1_BM25_COUNT
            CLASS_1_BM25_SUM
        and returns them as a dictionary.

        Parameters
        ----------
        result_df : DataFrame
            A query result dataframe produced by the query methods.
            Must have the columns:
                * score
                * class

        positive_class : str
            Specifies which 'class' is the positive class.
        '''
        df = result_df.copy()
        CLASS_0 = df.loc[(df['class'] != positive_class)]['score']
        CLASS_1 = df.loc[(df['class'] == positive_class)]['score']
        attrib_IR = {
            'CLASS_0_BM25_AVG': (0 if math.isnan(CLASS_0.mean())
                                 else CLASS_0.mean()),
            'CLASS_0_BM25_COUNT': CLASS_0.count(),
            'CLASS_0_BM25_SUM': CLASS_0.sum(),
            'CLASS_1_BM25_AVG': (0 if math.isnan(CLASS_1.mean())
                                 else CLASS_1.mean()),
            'CLASS_1_BM25_COUNT': CLASS_1.count(),
            'CLASS_1_BM25_SUM': CLASS_1.sum(),
        }
        return attrib_IR
    
    ...

    def insertArango(self, itemKey, itemBody):
        '''
        Inserts a document in the ArangoDB 'indexName' collection.

        Parameters
        ----------
        itemKey : str or number
            Document identifier

        itemBody : dict
            Document body/data.
        '''

        document = {'_key': itemKey}
        document.update(itemBody)
        self.arangoCollection.insert(document)
    
    ...

    def arango_query(self, query, ignore_first_result=False):
        '''
        Query ArangoDB view and returns a Pandas DataFrame with the results.

        Parameters
        ----------
        query : str
            Text to be queried to the view using BM25 analyzer.
        '''
        initial = time.time()
        escaped_query = str(query).replace('\\', '')
        escaped_query = str(escaped_query).replace("'", "\\\'")

        nResults = int(self.numberResults)
        if ignore_first_result:
            nResults += 1
        aqlquery = (f"FOR d IN {str(self.arangoViewName)} SEARCH "
                    + f"ANALYZER(d.text IN TOKENS('{escaped_query}'"
                    + f", 'text_en'), 'text_en') "
                    + f"SORT BM25(d, {self.bm25_k1}, {self.bm25_b}) "
                    + f"DESC LIMIT {nResults} "
                    + f"LET sco = BM25(d, {self.bm25_k1}, "
                    + f"{self.bm25_b}) RETURN {{ doc: d, score: sco }}")
        # print(aqlquery)
        cursor = self.arangoDb.aql.execute(query=aqlquery,
                                           count=True,
                                           batch_size=self.numberResults,
                                           optimizer_rules=['+all'],
                                           cache=True)
        item_list = []
        # print(1, time.time()-initial)
        initial = time.time()
        for item in cursor.batch():
            # print(item)
            item_list.append([item['score'], item['doc']['_id'].split('/')[-1],
                              item['doc']['class']])
        # print(2, time.time()-initial)
        if ignore_first_result and (len(item_list) > 0):
            item_list.pop(0)
        return pd.DataFrame(item_list, columns=['score', 'id', 'class'])
    
    ...
    
    def arango_get_IR_variables(self, query, positive_class='true', ignore_first_result=False):
        '''
         Query ArangoDB view and returns a dict with the IR variables.

        Parameters
        ----------
        query : str
            Text to be queried to the view using BM25 analyzer.
        '''
        result_df = self.arango_query(query, ignore_first_result=ignore_first_result)

        return self.calc_IR(result_df=result_df, positive_class=positive_class)

    ...