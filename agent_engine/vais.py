from google.cloud import discoveryengine_v1beta as discoveryengine
from google.api_core import exceptions
import os
from urllib.parse import quote 

import logging

# --- 環境変数 ---
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
LOCATION = os.getenv("LOCATION", "global")

USECASE_ENGINE_ID = os.getenv('USECASE_ENGINE_ID')
GCP_ENGINE_ID = os.getenv('GCP_ENGINE_ID')
ZENN_ENGINE_ID = os.getenv('ZENN_ENGINE_ID')
AI_AGENT_SUMMIT_ENGINE_ID = os.getenv('AI_AGENT_SUMMIT_ENGINE_ID')

# ----------------------------------------------------------


client = discoveryengine.SearchServiceClient()

def search_from_vais(
    query,
    serving_config,
    summary_spec=None,
):
    """ Vertex AI Search を使用して検索を実行し、結果を Markdown 形式で返す関数"""
    global client

    if not query:
        return '検索クエリを入力してください。'

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=5,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
                max_snippet_count=1
            ),
            summary_spec=summary_spec,
        )
    )

    try:
        response = client.search(request=request)
    except Exception as e:
        logging.info(str(e))
        return 'エラーが発生しました'
    output_md = ""

    if response.summary and response.summary.summary_text:
        output_md += f"## 概要:\n{response.summary.summary_text}\n\n---\n\n"

    output_md += "## 検索結果:\n"
    if not response.results:
        output_md += "関連する結果は見つかりませんでした。"
        return output_md

    for i, result in enumerate(response.results):
        doc = result.document
        title = doc.derived_struct_data.get('title', 'タイトルなし')
        link = doc.derived_struct_data.get('link', '')

        if link and link.startswith("gs://"):
            link = link.replace("gs://", "https://storage.cloud.google.com/", 1)

        encoded_link = quote(link, safe='/:?=&#') if link else ''
        snippet = ""
        if 'snippets' in doc.derived_struct_data and doc.derived_struct_data['snippets']:
            snippet = doc.derived_struct_data['snippets'][0].get('snippet', '')

        if encoded_link:
            output_md += f"### {i+1}. [{title}]({encoded_link})\n"
        else:
            output_md += f"### {i+1}. {title}\n"

        if snippet:
            snippet_md = snippet.replace("<em>", "*").replace("</em>", "*")
            output_md += f"{snippet_md}\n"
        output_md += "\n"

    return output_md


def search_from_vais_bq(
    query,
    serving_config,
):
    """ Vertex AI Search を使用して検索を実行し、結果を Markdown 形式で返す関数"""
    global client

    if not query:
        return '検索クエリを入力してください。'

    request = discoveryengine.SearchRequest(
        serving_config=serving_config,
        query=query,
        page_size=5,
        content_search_spec=discoveryengine.SearchRequest.ContentSearchSpec(
            snippet_spec=discoveryengine.SearchRequest.ContentSearchSpec.SnippetSpec(
                return_snippet=True,
                max_snippet_count=1
            ),
            summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
                summary_result_count=5,
                include_citations=False,
                model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                # set preamble
                # - 小学生でも理解できる表現で説明してください
                    preamble='要約には可能な限り、セッションの具体的な日時とURLリンクを含めるようにしてください。該当するセッションが複数あればそれぞれの情報を要約して出してください。URLリンクに関してはHTMLに target="_blank" を追加してクリック時に新規タブで開くようにしてください。',
                ),
                model_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelSpec(
                    version="gemini-2.5-flash/answer_gen/v1"
                ),
            ),
        ),
    )

    try:
        response = client.search(request=request)
    except Exception as e:
        logging.info(str(e))
        return 'エラーが発生しました'

    if response.summary and response.summary.summary_text:
        return response.summary.summary_text

def search_zenn(
        query: str
    ) -> str:
    """Zenn に検索を実行し、結果を Markdown 形式で返す関数"""
    serving_config = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/"
        f"engines/{ZENN_ENGINE_ID}/servingConfigs/default_serving_config"
    )
    return search_from_vais(
        query,
        serving_config,
    )


def search_gcp(
        query: str
    ) -> str:
    """Google Cloud Doc に検索を実行し、結果を Markdown 形式で返す関数"""
    serving_config = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/"
        f"engines/{GCP_ENGINE_ID}/servingConfigs/default_serving_config"
    )

    return search_from_vais(
        query,
        serving_config
    )


def search_usecase(
        query: str
    ) -> str:
    """事例 DB を使用して検索を実行し、結果を Markdown 形式で返す関数"""
    serving_config = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/"
        f"engines/{USECASE_ENGINE_ID}/servingConfigs/default_serving_config"
    )
    return search_from_vais(
        query,
        serving_config,
        summary_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec(
            summary_result_count=3,
            include_citations=True,
            model_prompt_spec=discoveryengine.SearchRequest.ContentSearchSpec.SummarySpec.ModelPromptSpec(
                preamble=""
            ),
        )
    )


def search_ai_agent_summit(
        query: str
    ) -> str:
    """Vertex AI Search の構造化データに検索を実行し、結果を Markdown 形式で返す関数"""
    serving_config = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/"
        f"engines/{AI_AGENT_SUMMIT_ENGINE_ID}/servingConfigs/default_serving_config"
    )

    return search_from_vais_bq(
        query,
        serving_config,
    )
