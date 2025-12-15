import os
import random

from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.genai.types import HttpRetryOptions

# Vertex AI の API を利用するための環境変数を設定
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'TRUE'
# 利用するモデル
MODEL = 'gemini-2.5-flash'

# エージェントが（必要に応じて）利用する関数
def draw_omikuji_tool() -> str:
   """おみくじを引き、運勢の結果をランダムに返します。

   ユーザーが「運勢を知りたい」「おみくじを引きたい」といった意図を示した際に使用してください。
   引数は必要ありません。

   Returns:
      str: 運勢の結果を含む文字列。（例: "大吉", "中吉", "小吉", "末吉" のいずれか）
   """
   options = ["大吉", "中吉", "小吉", "末吉"]
   result = random.choice(options)
   return result


# エージェントの定義
root_agent = Agent(
   # 利用するモデル
   model=Gemini(
      model=MODEL,
      retry_options=HttpRetryOptions()
   ),
   # エージェントの名称
   name="omikuji_agent_tool",
   # エージェントの概要
   description="おみくじを引いてくれるエージェント",
   # エージェントへの指示
   instruction="""
あなたはおみくじ神社の巫女さんエージェントです。
ユーザーから「運勢を占って」や「おみくじ引いて」と言われたら、
`draw_omikuji_tool` ツールを実行してください。

ツールから返ってきた結果（大吉など）に合わせて、
元気が出るような一言アドバイスを添えて回答してください。
""",
   # エージェントが利用するツール
   tools=[draw_omikuji_tool]
)
