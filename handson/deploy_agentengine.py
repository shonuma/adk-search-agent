import os

import vertexai
from dotenv import load_dotenv

load_dotenv('agent_engine/.env')

# 設定が必要な変数
USECASE_ENGINE_DATASTORE_ID = os.environ['USECASE_ENGINE_DATASTORE_ID']
GCP_ENGINE_DATASTORE_ID = os.environ['GCP_ENGINE_DATASTORE_ID']
SERVICE_ACCOUNT = os.environ['SERVICE_ACCOUNT']
GCP_PROJECT_ID = os.environ['GCP_PROJECT_ID']
SUMMARY_BUCKET_NAME = os.environ['SUMMARY_BUCKET_NAME']
# global で OK
LOCATION = 'global'

client = vertexai.Client(
    project=GCP_PROJECT_ID,
    location='us-central1',
)

from agent_engine.agent import root_agent as search_agent

# Agent Engine へデプロイするために必要な設定
remote_agent = client.agent_engines.create(
    agent=search_agent,
    config={
        "display_name": 'adk_search_agent',
        "staging_bucket": f'gs://{GCP_PROJECT_ID}-staging-bucket',
        # 動作に必要なライブラリ
        "requirements": [
            'google-adk==1.18.0',
            'google-cloud-aiplatform[adk,agent_engines]==1.132.0',
            'google-cloud-discoveryengine==0.13.12',
            'google-api-core==2.28.1',
            'fire==0.7.0',
            'uvicorn',
            'google-cloud-storage==3.7.0',
            'cloudpickle==3.1.2',
            'pydantic==2.11.7',
        ],
        # 送信する環境変数
        "env_vars": {
            "GCP_PROJECT_ID": GCP_PROJECT_ID,
            "GOOGLE_GENAI_USE_VERTEXAI": "TRUE",
            "GCP_ENGINE_DATASTORE_ID": GCP_ENGINE_DATASTORE_ID,
            "USECASE_ENGINE_DATASTORE_ID": USECASE_ENGINE_DATASTORE_ID,
            "LOCATION": LOCATION,
            "SUMMARY_BUCKET_NAME": SUMMARY_BUCKET_NAME,
        },
        # 動作に利用するサービスアカウント
        "service_account": SERVICE_ACCOUNT,
        "agent_framework": "google-adk",
        # agent_engine ディレクトリに必要なファイルが設置されている
        "extra_packages": ["agent_engine"],
    },
)