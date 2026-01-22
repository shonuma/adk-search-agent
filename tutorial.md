# Agent Development Kit (ADK) と Vertex AI Search で作る高度な検索エージェント

## はじめに

本ハンズオンでは、Vertex AI Search を用いて独自の検索システムを構築し、それを ADK で構築したエージェントに統合します。
チュートリアルに記載された内容を元に進めていきますので、こちらの画面の内容をよく読みながらコマンドの入力や、画面上の操作を進めてください。

ハンズオンの説明は [GitHub 上のページ](https://github.com/shonuma/adk-search-agent/blob/main/tutorial.md) のページからでも参照が可能です。

準備ができたら、**開始** ボタンを押してください。

## ハンズオン前半

ハンズオンの前半では、今回の検索システムで利用する検索エンジンを作成していきます。

具体的には、以下の作業を進めていきます。
- API の有効化
- Cloud Storage バケットの作成
- 検索対象データの取得
- 検索対象データのベクトル化
- 検索エンジンアプリの作成

準備ができたら、**次へ** ボタンを押してください。

この画面の説明は読み返すことができます。読み返したい場合は **前へ** ボタンを押してください。

## チュートリアルを閉じてしまったら...

コンソール上のページ遷移等で、チュートリアル画面やシェル画面が閉じてしまう場合があります。
上記に遭遇した場合、Cloud Shell 上で以下のコマンドを実行することで再度表示することが可能です。
```bash
cd ~/adk-search-agent && teachme tutorial.md
```

上記のコマンドを実行することでチュートリアルが再度開きます。
途中まで進めていた場合は[本画面](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/resume_tutorial.png)のように再開しますか？と聞かれますので、**はい**を選択すると前回開いていたステップまで画面が復旧されます。


## 環境変数の設定確認

環境変数 `GOOGLE_CLOUD_PROJECT` に Google Cloud プロジェクト ID が設定されていることを確認します。
（以降、単に **プロジェクト ID** と表記します）

```bash
echo $GOOGLE_CLOUD_PROJECT
```
ご利用の環境の Google Cloud プロジェクト ID は [ラボのページ](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/gcp_project_id_01.png)や、[ダッシュボード](https://console.cloud.google.com/home/dashboard)から確認できます。

上記で、プロジェクト ID が表示されていない場合は、Cloud Shell の再起動をお試しください。

`gcloud` コマンドのデフォルトプロジェクトも確認しておきます。
```bash
gcloud config list project --format='value(core.project)'
```
上記で確認したプロジェクト ID が表示されていれば成功です。

## API の有効化
Google Cloud では、利用したい機能ごとに API の有効化を行う必要があります。ここでは、以降のハンズオンで利用する機能を事前に有効化しておきます。

今回のハンズオンでは以下のサービスを利用しますので、該当の API を有効化します。
- Vertex AI
- Vertex AI Search
- Cloud Storage

以下のコマンドを実行します。

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  storage.googleapis.com \
  discoveryengine.googleapis.com
```

`Operation ... finished successfully.` と表示されたら成功です。

## 検索エンジン作成に必要な権限の付与

ログインしているメールアドレスを `USER_ID` という環境変数に設定します。
ユーザー名は、ラボのページの[トップ画面](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/user_name_2)から確認できます。
以下のコマンドを実行してください。

```bash
export USER_ID=$(gcloud info --format='value(config.account)')
```

以下のコマンドで、ユーザー ID が出力されていれば成功です。
```bash
echo $USER_ID
```

上記を設定した後、以下のコマンドを実行して `Cloud Storage` にアクセスするための権限 (`roles/storage.objectUser`) を付与します。

```bash
gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} --member "user:${USER_ID}" --role=roles/storage.objectUser
```

これで、検索エンジン作成に必要な権限の付与は完了です。

## Cloud Storage バケットの作成

続いて、オブジェクト ストレージを作成しましょう。ここでは以下の二つの Cloud Storage バケットを作成します。
1. 事例 PDF データを設置するためのバケット
2. エージェントとのチャット履歴まとめを保存するためのバケット

## 事例 PDF データを設置するためのバケットの作成

まずは、事例 PDF データを設置するためのバケットを作成します。

`<プロジェクトID>-adk-search-agent-handson-pdfs` という名称の `Cloud Storage` バケットを作成します。

以下のバケットを作成するためのコマンドを実行してください。

```bash
gcloud storage buckets create gs://${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-pdfs --project ${GOOGLE_CLOUD_PROJECT}
```

以下のコマンドは、バケットの中身を閲覧するコマンドです。
現在はデータは入っていませんから、実行して何も表示されなければ作成に成功しています。
```bash
gcloud storage ls gs://${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-pdfs
```

## エージェントとのチャット履歴まとめを保存するためのバケットの作成

続いて、エージェントとのチャット履歴まとめを保存するためのバケットを作成しましょう。

`<プロジェクトID>-adk-search-agent-handson-summary` という名称の `Cloud Storage` バケットを作成します。

以下のコマンドを実行します。

```bash
gcloud storage buckets create gs://${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-summary --project ${GOOGLE_CLOUD_PROJECT}
```

以下のコマンドは、バケットの中身を閲覧するコマンドです。
先ほど同様データは入っていないため、実行して何も表示されなければ作成に成功しています。
```bash
gcloud storage ls gs://${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-summary
```

以下の方法で、Cloud Storage のバケットが作成されたことを確認できます。
1. 画面上部の検索バーに **Storage** と入力します。
2. 検索候補から **Cloud Storage** を選択します。
3. 画面左部のメニューから **バケット** を選択します。
4. `<プロジェクトID>-adk-search-agent-handson-pdfs`、及び`<プロジェクトID>-adk-search-agent-handson-summary`というバケットが一覧に表示されていることを確認します。

以上でバケットの作成手順は完了です。

## バケット名の取得

今回作成したバケットの名称を控えておきましょう。以下のコマンドを実行することで、バケット名を取得できます。

事例 PDF を格納するバケット名
```bash
echo ${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-pdfs
```

エージェントとのチャット履歴まとめを保存するバケット名
```bash
echo ${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-summary
```

## 事例 PDF データのコピー

続けて、作成した Cloud Storage バケットに、事例 PDF データをコピーしていきましょう。
事例 PDF データは 165 件あります。

以下のコマンドを実行します。

```bash
gcloud storage cp -r gs://dev-genai-handson-25q2-static/pdfs/*.pdf gs://${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-pdfs/
```

コマンドが終了したら、コピーが完了しています。
以下のコマンドを実行して、PDFのリストが表示されればコピーに成功しています。

```bash
gcloud storage ls gs://${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-pdfs/
```

データが 165 件あることは、以下のコマンドで確認できます。

```bash
gcloud storage ls gs://${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-pdfs/*.pdf | wc -l
```

これでデータの準備ができました。

続いて、検索エンジンを作成していきましょう。

## 検索エンジンの作成

本手順では、以下の二つの検索エンジンの作成を行います。
- 準備した事例 PDF データを検索するための検索エンジン
- Google Cloud の技術的な質問を検索するための検索エンジン

検索エンジンを作成するには、**検索対象のデータの作成（ベクトル化）** を行い、ベクトル化したデータを**検索するための機能** を設定します。

## AI Applications を開く

検索エンジンを作成するサービスを開きます。

コンソール画面上部の検索バーに `AI applications` と入力し、**AI applications** を選択して開きます。

[このような画面](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/activate_disc_apis.png)が表示されるので、赤枠内のボタンを押してサービスの利用に必要な API の有効化を実施しましょう。

一定時間待つと[アプリ作成画面](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/ai_application_top.png)が表示されます。この画面が表示されたら成功です。

## データストアの作成（事例）

まずは、検索対象のデータのベクトル化を行っていきましょう。
本手順の画面キャプチャは、ラボのページに記載がありますのでそちらも参考にしてください。

1. 画面左部メニューの **データストア** を選択し、画面上部の **データストアを作成** を選択します。
2. データソースを選択する画面が表示されるので、`Cloud Storage` を選択します。
3. Cloud Storage のデータのインポート設定が表示されます、今回は PDF データを利用するので、`非構造データ - ドキュメント` を選択します。同期の頻度は `1 回限り` に設定します。
4. インポートするフォルダまたはファイルを指定します。先ほど作成した Cloud Storage バケット名（`<プロジェクトID>-adk-search-agent-handson-pdfs`）を指定します。または、**参照** から、バケットの一覧から[選択](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/vais_choose_pdfs.png)していただいても大丈夫です。
5. ⚠️**このとき、事例 PDF が格納されたバケット（-pdf）を選択してください。チャット履歴まとめを保存するバケット（-summary で終わるバケット名）を指定してしまうと正しくデータストアが作成されません**
6. **続行** を押します。
7. 名称、及びデータのローケーションを設定します。ロケーションは `global` を選択し、データストア名を `adk-search-agent-handson-gcs` に指定します。
8. 料金モデルを「全般的な料金」に設定します。完了したら、**作成** を押します。

以上で、データストアの作成（ベクトル化）は完了です。

データストアの作成には 数分 〜 10 分程度の時間がかかります。

## 検索エンジンの作成（事例）

続いて、検索エンジンを作成します。
本手順の画面キャプチャは、ラボのページに記載がありますのでそちらも参考にしてください。

1. 画面左部メニューの **アプリ** を選択し、画面上部の **アプリを作成する** を選択します。
2. アプリの種類で、**カスタム検索（一般）** の **作成** ボタンをクリックします。
3. アプリの構成の検索で、**Enterprise エディションの機能、生成レスポンス** が有効化されていることを確認します（チェックされていればそのままでOKです）。
4. アプリ名を `adk-search-agent-handson-gcs-app` に設定します。
5. 会社名または組織名には `Google Cloud` と入力します。
6. アプリのロケーションは `global` のままで **続行** を押します。
7. データストアの選択画面が表示されます。先ほどの手順で作成した `adk-search-agent-handson-gcs` を指定します。**続行** を押します。
8. 料金モデルを「全般的な料金」に設定します。完了したら、**作成** を押します。

アプリが正常に作成されました、とポップアップが表示されたら成功です。

アプリの作成が完了し動作し始めるには、10 分程度の時間がかかります。
待ち時間の間、もう一つのデータストア、検索エンジンを作成します。

## データストアの作成（Google Cloud ドキュメント）

それでは、Google Cloud のドキュメントを検索するための検索エンジンを作成していきましょう。
画面左上部の **AI Application** をクリックすると、アプリ、データストアの管理画面に戻ります。

1. 画面左部メニューの **データストア** を選択し、画面上部の **データストアを作成** を選択します。
2. データソースを選択する画面が表示されるので、`ウェブサイトのコンテンツ` を選択します。
3. データストアのウェブサイトの指定画面が表示されます。
4. ウェブサイトの高度なインデックス登録は **チェックしないでください**。（初期状態のままでOK）
5. インデックスに登録する URL パターンに `cloud.google.com/*` を指定します（除外するサイトは空のままでOK）。
6. 上記のように設定できたら（[設定例](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/google_cloud_search_02.png)）、続行を押します。
7. データストアの名称を `adk-search-agent-handson-web` に設定し、**続行** を押します。
8. 料金モデルが「全般的な料金」に設定されていることを確認し、**作成** を押します。

以上で、データストアの作成（ベクトル化）は完了です。続けて検索エンジンを作成していきましょう。

## 検索エンジンの作成（Google Cloud ドキュメント）
検索エンジンは、先ほどの事例データの手順とほぼ同様です。

1. 画面左部メニューの **アプリ** を選択し、画面上部の **アプリを作成する** を選択します。
2. アプリの種類で、**カスタム検索（一般）** の **作成** ボタンをクリックします。
3. アプリの構成の検索で、**Enterprise エディションの機能、生成レスポンス** が有効化されていることを確認します（チェックされていればそのままでOKです）。
4. アプリ名を `adk-search-agent-handson-web-app` に設定します。
5. 会社名または組織名には `Google Cloud` と入力します。
6. アプリのロケーションは `global` のままで **続行** を押します。
7. データストアの選択画面が表示されます。先ほどの手順で作成した `adk-search-agent-handson-web` のチェックボックスを有効にしたら、**続行** を押します。
8. 価格について `全般的な料金` が設定されていることを確認し、**作成** を押します。

「アプリが正常に作成されました」とポップアップが表示されたら成功です。

アプリの作成が完了し動作し始めるには 10 分程度の時間がかかります。

これで、二つの検索エンジンの作成が完了しました。

## 検索のプレビュー画面（事例）

作成した検索エンジンの動作確認を行ってみましょう。
画面左上部の **AI Application** をクリックすると、アプリ、データストアの管理画面に戻ります。

1. アプリの一覧から `adk-search-agent-handson-gcs-app` （事例検索）を選択します。
2. 左メニューから `プレビュー` を選択します。

検索ウィンドウが表示されるので、適当な検索ワードを入力して検索を行ってみましょう。結果が表示されたでしょうか？
- Cloud Run の事例
- ゲーム業界の事例

アプリの準備ができていない場合 `検索プレビューの準備がまだできていません` とエラーが表示されたり、結果が一件も表示されないことがあります。しばらく待ってから、再度検索をお試しください。

一定時間経過すると、検索結果の要約及び検索結果が表示されるようになります。

## 検索のプレビュー画面（Google Cloud ドキュメント）
続けて、Google Cloud ドキュメントの検索エンジンの動作確認も行ってみましょう。
画面左上部の **AI Application** をクリックすると、アプリ、データストアの管理画面に戻ります。

1. アプリの一覧から `adk-search-agent-handson-web-app` を選択します。
2. 左メニューから `プレビュー` を選択します。

検索ウィンドウが表示されるので、適当な検索ワードを入力して検索を行ってみましょう。結果が表示されたでしょうか？
- Cloud Run
- Google Kubernetes Engine

アプリの準備ができていない場合 `検索プレビューの準備がまだできていません` とエラーが表示されたり、結果が一件も表示されないことがあります。しばらく待ってから、再度検索をお試しください。

一定時間経過すると、検索結果が表示されるようになります。

## ここまでのまとめ
ここまでで、以下を作成しました。
- Google Cloud の事例を検索できるデータストア、及び検索エンジン
- Google Cloud のドキュメントを検索できるデータストア、及び検索エンジン

## ハンズオン前半の完了

ハンズオン前半は以上で終了です。お疲れ様でした！

## ハンズオン後半に入る前に…

Cloud Shell の画面を[閉じて](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/close_cloud_shell.png)、再度開いておきましょう。

## ハンズオン後半

ハンズオンの後半では、さきほど作成した検索システムをアプリケーションに組み込み、コンテナ化して Cloud Run にデプロイを行います。

具体的には、以下の作業を進めていきます。
- ADK を利用したエージェントの解説
- ADK を利用したエージェントの開発
- ADK を利用したエージェントへ検索エンジンを組み込む
- エージェントを、Agent Engine へのデプロイ
- Agent Engine プレイグラウド上で、エージェントの動作確認を実施

準備ができたら、**次へ** ボタンを押してください。

## ADK エージェントの構造

ADK を利用したエージェントの開発を進める前に、プログラムの構造を理解しましょう。
リポジトリには ADK を利用したエージェントの簡単なサンプルコードが用意されていますので、コードを見ながら理解していきます。

以下のコマンドを Cloud Shell 上で実行してください。
```bash
cloudshell edit ~/adk-search-agent/handson/omikuji_agent/agent.py
```

少し待った後、[エディタ画面](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/cloud_shell_screen.png)が表示されたら成功です
エディタ画面は、[矢印ボタン](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/maximize_editor.png)を押すことで最大化することも可能です（もう一度押すともとに戻る）。

エディタの画面に慣れていない、不安な方は、[こちら](https://github.com/shonuma/adk-search-agent/blob/main/handson/omikuji_agent/agent.py) をクリックしてブラウザ上でソースコードを確認することも可能です。

ソースコード が確認できたら、次のステップへ進みましょう。

## ADK エージェントの本体

`agent.py` のソースコードの[28 行目 〜 46 行目](https://github.com/shonuma/adk-search-agent/blob/main/handson/omikuji_agent/agent.py?hl=ja#L28-L46)を確認します。

上記はエージェントのインスタンスを作成する処理で、`Agent` クラスにパラメータを渡しています。それぞれのパラメータの意味について理解しましょう。
- `model`: エージェントが利用する生成 AI モデルを定義します。
- `name`: エージェントの名称を定義します。
- `description`: エージェントの概要を定義します。
- `instruction`: エージェントへの指示を定義します。
- `tools`: エージェントが利用するツールを定義します。

上記のうち、エージェントの挙動に関わる特に重要な項目（三点）について補足します。

### description
エージェントの概要です。
`description` は本エージェントが何者であるかを知るための説明（外向けの説明）になります。
人間がエージェントの概要を確認できるほか、他のエージェントが **本エージェントの機能を知る** ために重要です。

本サンプルでは「おみくじを引くエージェント」と役割を説明しています。

### instruction
エージェントの具体的な挙動を定義します。
`instruction` は、**本エージェント自身へ向けた、エージェントがどう振る舞うべきかの説明**（内向けの説明）になります。

以下の内容が含まれていることが望ましいです。
1. エージェントの名称
2. どのような指示を受け付けるか
3. 指示に対してどのように動作するか
4. （ツールを設定した場合）どのような場合にツールを利用するか
5. どのような結果を応答するか

本サンプルでは「このエージェントはおみくじを引くことができる」「おみくじを引く処理を実行するための条件」「ツールの利用条件」を指示しています。

### tools
エージェントが利用するツール（関数）を定義します。
例えばプログラム的な処理を実行したり、外部 API を実行したりできます。
エージェントがツールの用途を理解するためには、ツール側に記載された関数の説明文（`docstring`）も重要です。

本サンプルでは、おみくじの結果を取得するため、乱数を利用した関数を指定しています。

上記の `description`、`instruction`、`tools` について確認できたら、[ターミナル画面に戻り](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/return_to_terminal.png)ます。
次のステップへ進みましょう。

## もしソースコードを誤って編集してまったら...
エディタ画面でソースコードを書き換えてしまい元に戻せなくなってしまった...そんな場合は、以下のコマンドを実行することで、最初の状態に戻すことができます。

```bash
cd ~/adk-search-agent && git checkout .
```

## Cloud Shell 上でエージェントを動作させる

上記のエージェントの動作確認を行ってみましょう。

ADK にはエージェントの動作確認を実施できる GUI (Graphical User Interface) が用意されています。

まずは、動作確認に必要なライブラリをインストールします。以下のコマンドを実行してください。
```bash
sudo pip install -r ~/adk-search-agent/handson/requirements.txt
```

しばらく待つとインストールが完了します。
インストールが完了したら、以下のコマンドを実行します。

```bash
cd ~/adk-search-agent/handson
adk web
```

実行してしばらく待つと、サーバーが起動します。
[サーバーが起動している例](https://storage.cloud.google.com/dev-genai-handson-25q2-static/images/adk_web_local.png)
※ コマンド実行時、上記のスクリーンショットのように警告が表示される可能性がありますが、今回のハンズオンでは問題ないため、無視して大丈夫です。

ログの一番最後の行の `http://127.0.0.1:8000/` がクリックできるようになっていますので、クリックします。
- `INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`

新しいタブで　Web　ページが表示されたら成功です。

## 動作確認

動作確認を行ってみましょう。
表示されたウェブページ左上部に `Select an agent` と書かれた「エージェントのディレクトリを選択するセレクター」がありますので、そちらをクリックし、[omikuji_agent](https://storage.cloud.google.com/dev-genai-handson-25q2-static/images/omikuji_agent.png) を選択します。

選択できたら[右下部のテキストウィンドウ](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/talk_with_omikuji_agent.png)に以下のような質問をしてみましょう。
- こんにちは
- おみくじを引きたいです

おみくじの結果が表示されたでしょうか？
無事表示されたら動作確認完了です。

サーバーを停止するには、[ターミナル画面を開き](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/close_editor_and_open_console.png)、`Ctrl + c`（Ctrl キーを押しながら、C キーを押す） を押します。
[本画面のように入力待ちになっていれば](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/exec_control_plus_c)OKです。

`Ctrl + c` をうまく入力できない場合は、以下の手順でも停止できます。
1. エディタを開くボタンの右側にある`キーの組み合わせを送信` ボタンを押します。
2. 一番下の `キーの組み合わせを送信` を押します。
3. 装飾キーに `Ctrl` を、キーに `c` を入力します。[入力例](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/ctrl%2Bc_03.png)

⚠️ エラーに遭遇したら

Cloud Shell の認証が切れてしまっていると、チャット送信時に[このようなメッセージがポップアップ](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/error_in_agent.png) されることがあります。上記に遭遇したら、サーバーを停止したあと Cloud Shell を閉じて開き、エージェントの起動を行ってみてください。

動作確認が完了しサーバーが停止できたら、検索エージェントの実装にうつっていきましょう。

## 検索エージェントの構造を理解する
まず、検索エージェントのソースコードを確認してみましょう。

[Webページでソースコードを開く](https://github.com/shonuma/adk-search-agent/blob/main/handson/agent_engine/agent.py)か、以下のコマンドを Cloud Shell 上で実行してください。
```bash
cloudshell edit ~/adk-search-agent/handson/agent_engine/agent.py
```

本ソースコードで定義されているエージェントを簡単に解説します。

### 必要な環境変数について
本エージェントを動作させるには、以下の環境変数の設定が必要です。
- `PROJECT_ID`: Google Cloud のプロジェクトID
- `USECASE_ENGINE_DATASTORE_ID`: Google Cloud の事例を取得するためのデータストアの ID
- `GOOGLE_CLOUD_SEARCH_ENGINE_ID`: Google Cloud の技術的な質問に回答するためのデータストアの ID
- `SUMMARY_BUCKET_NAME`: 会話まとめを保存するための Cloud Storage バケット

これらの環境変数については、次のステップで設定を行います。

### root_agent（もりのくまさん）
ユーザーからの質問を受け付けるエージェントです。
ユーザーからの質問の内容に応じて、他のエージェントの呼び出しを行います。

`sub_agents` に `jirei_agent`、`gcp_doc_agent` そして `summary_agent` が定義されていることで、適切なエージェントを呼び出すことができます。

### jirei_agent（やまのたぬきさん）
Google Cloud の事例に関する質問に回答するエージェントです。
ハンズオン前半に作成した、Cloud Storage をナレッジとして回答を行います。

`tools` に `VertexAiSearchTool` が指定されています。
`VertexAiSearchTool` は、Vertex AI Search で作成した検索エンジンを利用できるツールであり、今回作成したデータストアの ID を指定することで、データの検索を可能にしています。

### gcp_doc_agent（うみのいるかさん）
Google Cloud の技術に関する質問に回答するエージェントです。
ハンズオン前半に作成した、ウェブサイトのコンテンツをナレッジとして回答を行います。

`jirei_agent` と同様に、`tools` に `VertexAiSearchTool` が指定されていますので、今回作成したデータストアの ID の指定が必要になります。

### summary_agent（まとめるねこさん）
ユーザーからの質問、エージェントからの回答をまとめるエージェントです。
`tools` に `save_to_gcs` という独自関数が設定されており、関数内で Cloud Storage にレポートのアップロードを行っています。

上記が確認できたら、ターミナル画面に戻りましょう。

## （再掲）もしソースコードを誤っていじってしまったら...
エディタ画面でソースコードをいじってしまって戻せなくなってしまった...そんな場合は、以下のコマンドを実行することで、最初の状態に戻すことができます。

```bash
cd ~/adk-search-agent && git checkout .
```

## 必要な環境変数の設定
それでは、動作に必要な環境変数を設定していきましょう。

[1] Google Cloud プロジェクト ID

以下のコマンドを実行してください。
```bash
export GCP_PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
```

続けて、アプリケーションから実行する検索エンジンの `データストア ID` を取得します。**アプリ ID** ではなく**データストアの ID** であることに注意してください。

1. 上部の検索バーに `AI applications` と入力し、**AI applications** を選択して開きます。
2. 画面左部メニューの **データストア** を選択します。
3. 画面右部に表示されているデータストアの `adk-search-agent-handson-gcs`, `adk-search-agent-handson-web` の情報 **ID** に表示されている文字列を控えておきます。これが `データストアの ID` となり、通常はそれぞれ `adk-search-agent-handson-gcs_xxxx`, `adk-search-agent-handson-gcs_web`  のような形式の文字列です。

[2] **Google Cloud 事例の検索エンジン** の `データストア ID` を `<id>` に設定します。`adk-search-agent-handson-gcs_xxxx` のような形式の文字列になります。
```bash
export USECASE_ENGINE_DATASTORE_ID=<id>
```

[3] **ウェブサイトの検索エンジン** の `データストア ID` を `<id>` に設定します。`adk-search-agent-handson-web_xxxx` のような形式の文字列になります。
```bash
export GCP_ENGINE_DATASTORE_ID=<id>
```

[4] 回答をまとめた結果を設置する Cloud Storage バケット名を設定します。
```bash
export SUMMARY_BUCKET_NAME=${GOOGLE_CLOUD_PROJECT}-adk-search-agent-handson-summary
```

[5] エージェントを Agent Engine 上で動作させるサービスアカウントの指定
エージェントを Agent Engine 上で動作させる際に必要な環境変数です。サービスアカウントの作成は後ほど実施します。
```bash
export SERVICE_ACCOUNT=adk-search-agent-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com
```

上記が設定されたことを確認するために、以下のコマンドを実行してください。
```bash
echo GCP_PROJECT_ID=${GCP_PROJECT_ID}
echo USECASE_ENGINE_DATASTORE_ID=${USECASE_ENGINE_DATASTORE_ID}
echo GCP_ENGINE_DATASTORE_ID=${GCP_ENGINE_DATASTORE_ID}
echo SUMMARY_BUCKET_NAME=${SUMMARY_BUCKET_NAME}
echo SERVICE_ACCOUNT=${SERVICE_ACCOUNT}
```

変数は正しく設定されているでしょうか。
一つでも欠けていたり、誤って指定されていると正しく動作しないため、よく確認を行ってみてください。
全て正しく設定されていることを確認したら、次のステップへ進みましょう。

## 環境変数を .env ファイルに保存する

環境変数はターミナルを閉じると削除されてしまいます。そのため、環境変数をファイルとして保存しておきましょう。
以下のコマンドを実行します。
```bash
bash ~/adk-search-agent/handson/save_env_vals.sh
```

以下のコマンドを実行して、変数が格納されていれば OK です。
```bash
cat ~/adk-search-agent/handson/agent_engine/.env
```

## Cloud Shell 上での動作確認
変数が正しく設定されているかを確認するために、動作確認を行いましょう。

以下のコマンドを実行します。
```bash
cd ~/adk-search-agent/handson
adk web
```
先ほどと同様にログの末尾の `http://127.0.0.1:8000` がクリック可能になっていますので、クリックして Web ページを開きます。
今度は画面左上部の選択で `agent_engine` を指定します。

以下のような質問を試してみましょう。
- `こんにちは`: もりのくまさん（受付）が回答
- `Cloud Run の事例を教えて`: やまのたぬきさん（事例検索エージェント）が回答
- `Cloud Run の価格を教えて`: うみのいるかさん（Google Cloud 技術エージェント）が回答
- `これまでの結果をまとめて`: まとめるねこさん（結果をまとめるエージェント）が回答

Cloud Shell 上で実行してる関係上、以下のような問題が起きるかもしれません。
- 回答が遅い（10秒以上待つ）
- 回答が来ないことがある

上記のような問題はデプロイで解決する可能性があるため、このタイミングでは正しいレスポンスが帰ってくれば OK としてください。

何度質問しても結果が帰ってこない場合は、環境変数の設定が誤っている可能性があります。

特に、結果が帰ってこなくなり、コンソール画面が[この表示](https://storage.googleapis.com/dev-genai-handson-25q2-static/images/error_by_env_vals.png)のようになっている場合は、環境変数が正しく設定されていない可能性が高いです。正しく環境変数が設定されているか、前の手順を見直してみてください。

動作確認が終了したら、ターミナル画面に戻って `Ctrl+C` を実行します。
次のステップへ進みましょう。

## エージェントが利用するサービスアカウントの作成
Agent Engine 上へデプロイするエージェントが利用するサービスアカウントを作成しておきましょう。

```bash
gcloud iam service-accounts create adk-search-agent-sa --display-name "Service Account for ADK Search Agent" --project ${GOOGLE_CLOUD_PROJECT}
```

`Created service account adk-search-agent-sa` と表示されれば成功です。

続いて、必要な権限を付与していきます。サービスアカウントには、以下が実施できるように適切な権限を付与します。
- Cloud Storage への書き込み
- AI サービスの利用
- 検索エンジンの利用
- ログの書き込み

```bash
for role in roles/storage.objectUser roles/discoveryengine.user roles/aiplatform.user roles/logging.logWriter roles/serviceusage.serviceUsageConsumer;do gcloud projects add-iam-policy-binding ${GOOGLE_CLOUD_PROJECT} --member="serviceAccount:adk-search-agent-sa@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" --role=${role}; done;
```

これで、サービスアカウントの準備ができました。

## Agent Engine へのデプロイ
サービスアカウントが生成できたら、いよいよデプロイを実行します。

以下のコマンドを実行します。
```bash
cd ~/adk-search-agent/handson && bash ~/adk-search-agent/handson/deploy_agentengine.sh
```

実行にはしばらく時間がかかります。
その間に、デプロイコマンドを確認してみましょう。[デプロイスクリプト](https://github.com/shonuma/adk-search-agent/blob/main/handson/deploy_agentengine.py)を確認します。

### 環境変数の設定
以下の環境変数を読み込んでいます。事前に `export` コマンドで設定しておくか、先ほど作成した `.env` ファイルに環境変数を設定しておきます。

- `USECASE_ENGINE_DATASTORE_ID`
- `GCP_ENGINE_DATASTORE_ID`
- `SERVICE_ACCOUNT`
- `GCP_PROJECT_ID`
- `SUMMARY_BUCKET_NAME`

### remote_agent
デプロイするエージェントの情報を記載します。
`agent` パラメータには `search_agent` が設定されており、これは `from agent_engine.agent import root_agent as search_agent` と記載があるため、先ほど動作確認を行っていたエージェントのインスタンスであることがわかります。

### config
エージェントの付加情報です。今回のエージェントでは、以下を指定しています。
- `display_name`: Agent Engine 上で表示される名称です。
- `staging_bucket`: デプロイに必要なファイルを一時的に設置する Cloud Storage バケットです。自動的に作成されます。
- `requirements`: エージェントの動作に必要なライブラリとバージョンを指定します。
- `env_vars`: エージェントの動作に必要な環境変数を指定します。
- `service_account`: エージェントの動作に利用するサービスアカウントを指定します。
- `agent_framework`: エージェントのフレームワークを指定します。今回は ADK を利用しているので `googl-adk` を指定しています。
- `extra_packages`: エージェントのファイルが格納されているディレクトリを指定します。実行しているスクリプトから見た相対パスを記載します。

何もメッセージが表示されず、ターミナルが入力待ちになれば、デプロイ完了です。

## デプロイされたサービスの動作確認
デプロイが完了したら、実際にデプロイされたエージェントを Agent Engine サービスから確認してみましょう。

1. 上部の検索バーに `Agent Engine` と入力し、**Agent Engine** を選択して開きます。
2. デプロイされたエージェントの一覧が表示されています。**adk_search_agent** をクリックして開きます。
3. 上部メニューから **プレイグラウンド** を選択して開きます。
4. 画面右下にテキストボックスが表示されますので、以下のような質問をしてみましょう。

- こんにちは
- BigQuery の事例を教えて
- BigQuery の価格を教えて
- これまでの結果をまとめて

それぞれの質問に対して、結果が取得できれば成功です。

## Congratulations! (ハンズオンの完了)

ハンズオンは以上で終了です。お疲れ様でした！

画面右上部の **✕ボタン** を押して、チュートリアルを閉じることができます。

本環境は Google Cloud で用意された環境のため、シークレットウィンドウをそのまま閉じていただいて OK です。タイマー終了時までは、本環境を自由にお触りいただけます。