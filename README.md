# Learn Cisco Modeling Labs 2

Cisco Modeling Labs 2（CML2）向けの学習ラボを置くリポジトリです。

## ラボ一覧

| ラボ | 内容 | インポートファイル |
| --- | --- | --- |
| [BGP / iBGP / OSPF 冗長](labs/bgp-redundant/README.md) | デュアルホーム eBGP、ISP コアの OSPF + iBGP、ユーザ PC によるエンドツーエンド確認 | [`labs/bgp-redundant/bgp-ibgp-ospf-redundant.yaml`](labs/bgp-redundant/bgp-ibgp-ospf-redundant.yaml) |

## 使い方（共通）

1. CML2 の Lab Manager で **Import** を選び、各ラボの YAML を取り込む
2. 必要なノード定義（本ラボは `iosv` / `alpine` / `unmanaged_switch`）とイメージがサーバにあることを確認する
3. ラボを Start し、各 README の確認手順に沿って OSPF / BGP / ping を見る

コンソールおよび Alpine の初期アカウントは `cisco` / `cisco` です。
