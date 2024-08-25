# ecr-deployman

ECR のイメージリポジトリを監視して、新しいイメージがプッシュされたら、Kubernetes にデプロイします。

Github アカウントは必要ありません。

ECR のイメージを Push できる権限を持つ IAM と、その認証トークンが必要です。

主に社内サーバーで Kubernetes を運用している場合に適しています。

## 想定される環境

- Github Workflow で Docker イメージをビルドしている
- ビルドされたイメージを ECR にイメージをプッシュしている
- Kubernetes の Deployment は latest タグで運用している
- Kubernetes は社内サーバーで運用している
- Slack を使っている

それ以外の環境では有効ではありません。

## 動作仕様

YAML で設定ファイルを書き、それを ConfigMap として K8s にデプロイし、それをマウントしてこのイメージの Pod を起動します。

設定されている ECR リポジトリの特定のイメージタグを 1分ごとに監視し、変更があれば Deployment の アノテーション
`spec.template.metadata.annotations.imageUpdatedAt` をイメージの Push日時に変更します。

K8s は、マニフェストの変更を検知し、Pod を更新します。

## config.yml

```yaml
awsEcrCredentials:
  - name: primary-ecr-credential
    awsAccessKeyId:
      fromEnv: AWS_ACCESS_KEY_ID
    awsSecretAccessKey:
      fromEnv: AWS_SECRET_ACCESS_KEY
    # 直接指定することも可能
    # awsAccessKeyId: AKIA...
    # awsSecretAccessKey: ......
    regionName: ap-northeast-1
    namespace: my-k8s-namespace
    secretName: ecr-credential
    # ローカルで実行する場合の kubeconfig の設定。
    # Pod で実行する場合は不要
    # kubeConfigFile: /Users/myname/.kube/config-mycluster
    # kubeConfigContext: None

deployments:
  - deploymentName: my-app-deployment-name
    repositoryPrefix: 000000000000.dkr.ecr.ap-northeast-1.amazonaws.com
    repositoryName: ytyng/my-app
    imageTag: latest
    namespace: my-k8s-namespace
    credentialName: primary-ecr-credential
    slackNotification:
      webhookUrl: https://hooks.slack.com/services/my-slack-webhook-url
      channel: "#my-channel"
      username: "ecr-deployman"
      iconEmoji: ":package:"
      # messagePrefix: "Some prefix message."
      messageSuffix: "https://www.ytyng.com/"
```
