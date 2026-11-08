# Learn Cisco Modeling Labs 2

Cisco Modeling Labs 2（CML2）向けの学習ラボを置くリポジトリです。  
This repository hosts hands-on labs for Cisco Modeling Labs 2 (CML2).

ラボの説明は **英語 (English)** と **日本語** の併記です。各ラボの `README.md` を見てください。  
Lab manuals are written in **English** and **日本語** (Japanese). See each lab `README.md`.

## Labs / ラボ一覧

| Lab / ラボ | Topic / 内容 | Languages / 言語 | Import file / インポート |
| --- | --- | --- | --- |
| [YANG / NETCONF / RESTCONF](labs/yang-netconf/README.md) | Model-driven management on IOS-XE (`csr1000v`), OSPF underlay, curl & `ncclient` examples | **EN + JA** | [`labs/yang-netconf/yang-netconf-restconf.yaml`](labs/yang-netconf/yang-netconf-restconf.yaml) |

## Common usage / 使い方（共通）

1. CML2 **Lab Manager → Import** で各ラボの YAML を取り込む / import the lab YAML  
2. 必要なノード定義とイメージがサーバにあることを確認する / confirm node definitions and images exist  
3. ラボを **Start** し、各 README の確認手順に従う / start nodes and follow that lab’s README  

Default credentials / 初期アカウント: `cisco` / `cisco`

### YANG lab notes / YANG ラボ補足

- Needs IOS-XE with YANG: prefer `csr1000v` (or `cat8000v` / IOL-XE). **`iosv` is not enough.**  
  YANG 対応の IOS-XE が必要です。`csr1000v`（または `cat8000v` / IOL-XE）を推奨。**`iosv` では不足**します。  
- Client examples: [`labs/yang-netconf/scripts/`](labs/yang-netconf/scripts/)  
- Full bilingual manual: [`labs/yang-netconf/README.md`](labs/yang-netconf/README.md)
