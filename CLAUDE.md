# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

ecr-deployman は ECR (Amazon Elastic Container Registry) のイメージリポジトリを監視し、新しいイメージが push されたら Kubernetes にデプロイするツールです。

主な機能:
- ECR リポジトリの監視（1分ごと）
- 新しいイメージ検出時の Kubernetes Deployment 自動更新
- Slack 通知
- 複数の ECR クレデンシャル・デプロイメント設定対応

## Project Structure

```
app/
├── main.py              # エントリーポイント、メインループ
├── config_loader.py     # YAML 設定ファイルのロード
├── credentials.py       # AWS ECR クレデンシャル管理
├── deployments.py       # Deployment 処理、ECR 監視、K8s 更新
├── kv_store.py         # シンプルな Key-Value ストレージ
├── logger.py           # ログ設定
├── message_utils.py    # Slack 通知メッセージ生成
└── storage/            # 永続化データ保存ディレクトリ

docker/
├── Dockerfile          # コンテナイメージビルド定義
├── build.sh           # ビルドスクリプト
├── config.sh          # Docker 設定（イメージ名等）
├── login.sh           # ECR ログイン
├── push-image.sh      # ECR へのプッシュ
└── run.sh             # ローカル実行

kubernetes/
└── pod.sample.yaml    # Pod 定義サンプル
```

## Development Commands

### 依存関係インストール
```bash
pipenv install
```

### ローカル実行
```bash
pipenv run python app/main.py
```

### Docker イメージビルド
```bash
cd docker
./build.sh
```

### ECR へのプッシュ
```bash
cd docker
./login.sh
./push-image.sh
```

### ローカル Docker 実行
```bash
cd docker
./run.sh
```

## Architecture Notes

### 監視フロー
1. `main.py` が 60秒ごとに各 deployment を処理
2. `deployments.py` の `process_deployment()` が ECR イメージの更新を確認
3. 更新がある場合、K8s Deployment の annotation を更新して Pod 再起動をトリガー
4. Slack 通知を送信

### 状態管理
- `SimpleKVStore` を使用してイメージの push 日時や Secret 更新日時を永続化
- `storage/` ディレクトリにファイルとして保存

### Kubernetes 連携
- ECR クレデンシャルを K8s Secret として自動作成・更新
- Deployment の `imageUpdatedAt` annotation を更新して Pod 再起動

### エラーハンドリング
- 各 deployment の処理は独立しており、1つが失敗しても他は継続
- エラーはログに記録され、次の周期で再試行

## Configuration

設定は `config.yaml` で管理:
- `awsEcrCredentials`: ECR アクセスのための AWS クレデンシャル設定
- `deployments`: 監視対象の ECR リポジトリと対応する K8s Deployment の設定

環境変数から AWS クレデンシャルを読み込むことも、直接設定に記述することも可能。

## Testing Approach

テスト用のスクリプトは `~scratch/` ディレクトリに配置:
- `test_kubernetes.py`: Kubernetes 接続テスト
- `test_webhook.py`: Slack webhook テスト
