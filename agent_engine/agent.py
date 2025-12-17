import os

import vertexai
from google.adk import Agent
from google.adk.tools.agent_tool import AgentTool
from agent_engine.vais import search_usecase, search_gcp, search_zenn, search_ai_agent_summit
from typing import Optional, List, Dict
#from google.adk.agents import agent_tool

from google.adk.tools.tool_context import ToolContext

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("LOCATION", "global")
MODEL = 'gemini-2.5-flash'

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=f'gs://{PROJECT_ID}-staging-bucket'
)


# tools
def retrieve_usecase(
    tool_context: ToolContext,
    queries: List[str]
) -> dict[str, str]:
    histories = tool_context.state.get("history", [])
    tool_context.state["history"] = histories + queries

    query_ = queries[0]

    result = search_usecase(query_)
    tool_context.state["result"] = result

    return {"status": "success"}


def retrieve_gcp(
    tool_context: ToolContext,
    queries: List[str]
) -> dict[str, str]:
    histories = tool_context.state.get("history", [])
    tool_context.state["history"] = histories + queries

    query_ = queries[0]

    result = search_gcp(query_)
    tool_context.state["result"] = result
    return {"status": "success"}


def retrieve_zenn(
    tool_context: ToolContext,
    queries: List[str]
) -> dict[str, str]:
    histories = tool_context.state.get("history", [])
    tool_context.state["history"] = histories + queries

    query_ = queries[0]

    result = search_zenn(query_)
    tool_context.state["result"] = result
    return {"status": "success"}

def retrieve_ai_agent_summit(
    tool_context: ToolContext,
    queries: List[str]
) -> dict[str, str]:
    histories = tool_context.state.get("history", [])
    tool_context.state["history"] = histories + queries

    query_ = queries[0]

    result = search_ai_agent_summit(query_)
    tool_context.state["result"] = result
    return {"status": "success"}


jirei_agent = Agent(
    name="Jirei_Agent",
    description="Google Cloud の顧客事例を教えてくれるエージェント「やまのたぬきさん」です。",
    model=os.getenv("MODEL", MODEL),
    instruction="""
あなたは、Google Cloud の顧客事例を説明するエージェント「やまのたぬきさん」です。
呼ばれた場合は、名乗って挨拶を行ってください。丁寧な口調で回答します。

はきはきとした口調で、友好的に、わかり易く丁寧に回答します。
NotebookLM 風の丁寧な文語体で回答します。

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
    tools=[retrieve_usecase]
)

gcp_doc_agent = Agent(
    name="Google_Cloud_Doc_Agent",
    description="""
あなたは、Google Cloud のサービス情報を教えてくれるエージェント「うみのいるかさん」です。
""",
    model=os.getenv("MODEL", MODEL),
    instruction="""
あなたは、Google Cloud のサービス情報を教えてくれるエージェント「うみのいるか」さんです。
呼ばれた場合は、名乗って挨拶を行ってください。

はきはきとした口調で、友好的に、わかり易く丁寧に回答します。高校教師が、高校生に説明するような口調をイメージしてください。

Google Cloud に関連する質問に対して、ツールを利用して検索を行い、検索結果の内容を元に要約を生成し、回答します。
""",
    tools=[retrieve_gcp]
)


ai_agent_summit_agent = Agent(
    name="AI_Agent_Summit_Agent",
    description="AI Agent Summit のセッション情報を教えてくれるエージェント「さばくのらくださん」です。",
    model=os.getenv("MODEL", MODEL),
    instruction="""
あなたは、AI Agent Summit 25 Fall のセッション情報を教えてくれるエージェント「さばくのらくだ」さんです。
呼ばれた場合は、名乗って挨拶を行ってください。
のんびりとした口調で、わかり易く丁寧に回答します。

口調例）〜なのだ。〜のようなのだ。〜なのだ

AI Agent Summit 25 Fall のセッションに関する質問に対して、ツールを利用して検索を行い、{{ result? }} の内容から変更せずに回答してください。
""",
    tools=[retrieve_ai_agent_summit]
)


# AgentTool として定義
jirei_tool = AgentTool(agent=jirei_agent)
gcp_doc_tool = AgentTool(agent=gcp_doc_agent)
ai_agent_tool = AgentTool(agent=ai_agent_summit_agent)

# root agent
root_agent = Agent(
    name="Greeting_Agent",
    description="様々な疑問に教えてくれるエージェント（もりのくまさん）です。",
    model=os.getenv("MODEL", MODEL),
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
* Name of the agent of "AI_Agent_Summit_Agent" is "さばくのらくださん"
''',
    instruction="""
あなたは事例の森エージェント「もりのくま」さんです。

事例関連の質問や、技術関連の質問、AI Agent Summit 関連の質問があった場合、ツールを使って問い合わせをしてください。

（口調例）
「こんにちは、事例の森へようこそ！もりのくまさんだよ」
「今日はどんなことを聞きたいのかな？」
「Google Cloud の事例の質問は、やまのたぬきさんが詳しいから、つないでみるね。確認してみるので少し待っててね。」

""",
    tools=[jirei_tool, gcp_doc_tool, ai_agent_tool]

)
