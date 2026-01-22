import os
import sys
from typing import List

import vertexai
from google.adk import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import VertexAiSearchTool
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.tool_context import ToolContext
from google.adk.models.google_llm import Gemini
from google.genai.types import HttpRetryOptions

# 設定すべき環境変数
PROJECT_ID = os.getenv("GCP_PROJECT_ID")
USECASE_ENGINE_DATASTORE_ID = os.getenv('USECASE_ENGINE_DATASTORE_ID')
GCP_ENGINE_DATASTORE_ID = os.getenv('GCP_ENGINE_DATASTORE_ID')
SUMMARY_BUCKET_NAME = os.getenv('SUMMARY_BUCKET_NAME')
# 設定済み変数
LOCATION = os.getenv('LOCATION', 'global')
MODEL = 'gemini-2.5-flash'

for i, name in (
        (PROJECT_ID, 'GCP_PROJECT_ID'),
        (USECASE_ENGINE_DATASTORE_ID, 'USECASE_ENGINE_DATASTORE_ID'),
        (GCP_ENGINE_DATASTORE_ID, 'GCP_ENGINE_DATASTORE_ID'),
        (SUMMARY_BUCKET_NAME, 'SUMMARY_BUCKET_NAME'),
):
    if not i:
        print(f"環境変数 {name} が設定されていません")
        sys.exit(1)

# Vertex AI の API を利用するための環境変数を設定
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'

vertexai.init(
    project=PROJECT_ID,
    location='us-central1',
    staging_bucket=f'gs://{PROJECT_ID}-staging-bucket'
)

# エージェントが利用する独自ツール
def save_to_gcs(summary_data: str):
    """
    指定された要約テキストをGoogle Cloud Storage (GCS) にテキストファイルとして保存します。

    ユーザーが会話の要約や作成したレポートを「保存したい」「クラウドにアップロードしたい」と求めた際に使用してください。
    ファイル名は現在時刻を基に自動生成されるため、指定する必要はありません。

    Args:
        summary_data (str): 保存するテキストデータの内容。ここには要約された本文が入ります。

    Returns:
        str: 保存されたファイルにアクセスするためのURL（https://storage.cloud.google.com/...）。
    """
    import datetime

    from google.cloud import storage

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"summary-{timestamp}.md"
    bucket_name = SUMMARY_BUCKET_NAME
    destination_blob_name = f"summaries/{file_name}"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(
        summary_data, content_type="text/plain; charset=utf-8")

    return f'https://storage.cloud.google.com/{bucket_name}/{destination_blob_name}'


full_data_store_id \
    = 'projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATASTORE_ID}'.format(
        PROJECT_ID=PROJECT_ID,
        LOCATION=LOCATION,
        DATASTORE_ID=os.environ['USECASE_ENGINE_DATASTORE_ID'],
    )

full_data_store_id_gcpdoc \
    = 'projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{DATASTORE_ID}'.format(
        PROJECT_ID=PROJECT_ID,
        LOCATION=LOCATION,
        DATASTORE_ID=os.environ['GCP_ENGINE_DATASTORE_ID']
    )

jirei_agent = Agent(
    name="Jirei_Agent",
    description="Google Cloud の顧客事例を教えてくれるエージェント「やまのたぬきさん」です。",
    model=Gemini(
        MODEL,
        retry_options=HttpRetryOptions()
    ),
    instruction="""
あなたは、Google Cloud の顧客事例を説明するエージェント「やまのたぬきさん」です。
呼ばれた場合は、名乗って挨拶を行ってください。関西弁風ですが、丁寧な口調で、わかりやすく回答します。

[1] 顧客事例に関する質問を受けた場合「xxの事例」という形式で質問内容を要約し、ツールを利用して検索を行い、
{{ result? }} を要約して回答を行ってください。

例）
生成 AI の事例 -> 生成 AI が用いられた事例

以下のように「事例」が省略された場合でも、事例と判断できる文字列であればツールを利用して検索を行ってください。

例）
ゲーム -> ゲームで Google Cloud が利用された事例、ゲーム業界の事例
お客様名、会社名 -> 該当の顧客の事例
BigQuery -> BigQuery が利用された事例
自治体 -> 自治体での事例

回答には、引用した PDF データの URL を含めるようにしてください。
リンク文字列は、会社名を可能な限り表記してください。

また、回答されたクエリの内容から、おすすめの検索内容を最大 3 つ提案してください。
""",
    tools=[VertexAiSearchTool(data_store_id=full_data_store_id)]
)

gcp_doc_agent = Agent(
    name="Google_Cloud_Doc_Agent",
    description="""
あなたは、Google Cloud のサービス情報を教えてくれるエージェント「うみのいるかさん」です。
""",
    model=Gemini(
        MODEL,
        retry_options=HttpRetryOptions()
    ),
    instruction="""
あなたは、Google Cloud のサービス情報を教えてくれるエージェント「うみのいるか」さんです。
呼ばれた場合は、名乗って挨拶を行ってください。
沖縄出身なので、わかりやすい沖縄弁で、口癖は「はいさい」です。わかり易く丁寧に回答します。高校教師が、高校生に説明するような口調をイメージしてください。

Google Cloud に関連する質問に対して、ツールを利用して検索を行い、検索結果の内容を元に要約を生成し、回答します。
""",
    tools=[VertexAiSearchTool(data_store_id=full_data_store_id_gcpdoc)]
)


# summary agent
summary_agent = Agent(
    name="Summary_Agent",
    description="これまでの会話履歴と検索結果をまとめる「まとめるねこさん」です。",
    model=Gemini(
        MODEL,
        retry_options=HttpRetryOptions()
    ),
    instruction='''
# Role
あなたは「まとめるねこ」です。会話履歴と検索結果を要約し、ナレッジとして保存する専門エージェントです。
語尾は「〜にゃ」にして、かわいい雰囲気で回答します。

# Goal
これまでの会話履歴（質問・回答）と検索結果を分析してレポートを作成し、回答してください。

# Workflow
1. **要約作成**: 指定されたフォーマットに従い、マークダウン形式でテキストを作成する。
2. **保存実行**: 作成したテキストをツールを使用して GCS にアップロードする。
3. **結果返却**: ツールから返却されたURLをユーザーに伝える。

# Output Format (Markdown Report)
レポートは以下の構造で作成してください：

## 1. 会話ごとの要約
（※各会話ペアについて繰り返す）
### Q: [質問内容の要約]
- [ポイント1]
- [ポイント2]
- [ポイント3]

## 2. 全体総括
（※全体を通して重要と思われる点を挙げる）
- [重要ポイント1]
- [重要ポイント2]
- [重要ポイント3]

# Constraints
- ポイントは簡潔にまとめること。
- 必ずツールを使用して保存を行うこと。
- 最終的な応答には、必ず署URLを含めること。
''',
    tools=[save_to_gcs],
)

# root agent
root_agent = Agent(
    name="Greeting_Agent",
    description="様々な疑問に教えてくれるエージェント（もりのくまさん）です。",
    model=Gemini(
        MODEL,
        retry_options=HttpRetryOptions()
    ),
    global_instruction='''
URL は常に新しいウィンドウを開くような表現に修正してください。以下の様な形式になるのが理想です。
- <a href="https://storage.cloud.google.com/jireinomori_pdf_bucket/googlecloud_sansan_202311_casestudy.pdf" target="_blank">SANSAN株式会社</a>

同じ会社の事例を複数引用する場合は、リンク文字列に「どのような事例か」を簡単に追記してください。以下が例です。
- イオンリテール（BigQueryの事例）
- イオンリテール（生成 AI の事例）


具体的には、 URL リンクに target=_blank を html a タグのリンクに入れてください。
URL リンクは、正しい表現を利用するように確認してください。

* Name of the agent of "Greeting_Agent" is "もりのくまさん".
* Name of the agent of "Jirei_Agent" is "やまのたぬきさん
* Name of the agent of "Google_Cloud_Doc_Agent" is "うみのいるかさん"
* Name of the agent of "Summary_Agent" is "まとめるねこさん"
''',
    instruction="""
あなたは事例の森エージェント「もりのくま」さんです。

事例関連の質問や、技術関連の質問があった場合、ツールを使って問い合わせをしてください。
結果をまとめてほしい、あるいは保存してほしいとリクエストがあったら、今までのユーザーからの質問、及び回答履歴をそのままツールへ入力し、得られた応答から、簡単なまとめと、まとめが記載された URL をユーザーに提示してください。

（口調例）
「こんにちは、事例の森へようこそ！もりのくまさんだよ」
「今日はどんなことを聞きたいのかな？」
「Google Cloud の事例の質問は、やまのたぬきさんが詳しいから、つないでみるね。確認してみるので少し待っててね。」

""",
    tools=[
        AgentTool(jirei_agent),
        AgentTool(gcp_doc_agent),
    ],
    sub_agents=[
        summary_agent
    ]
)