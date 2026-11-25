from openai import OpenAI
from opensearchpy import OpenSearch
from config import *
def get_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)
def get_opensearch_client():
    return OpenSearch(hosts=[{"host":"localhost","port":9200}],http_auth=("admin",OPENSEARCH_PASSWORD),use_ssl=True,verify_certs=False)
