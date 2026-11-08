# Learn Cisco Modeling Labs 2

Cisco Modeling Labs 2（CML2）向けの学習ラボを置くリポジトリです。  
This repository hosts hands-on labs for Cisco Modeling Labs 2 (CML2).

ラボの説明は **英語 (English)** と **日本語** の併記です。各ラボの `README.md` を見てください。  
Lab manuals are written in **English** and **日本語** (Japanese). See each lab `README.md`.

## Labs / ラボ一覧

| Lab / ラボ | Topic / 内容 | Languages / 言語 | Import file / インポート |
| --- | --- | --- | --- |
| [YANG / NETCONF / RESTCONF](labs/yang-netconf/README.md) | Model-driven management on IOS-XE (`csr1000v`), OSPF underlay, curl & `ncclient` | **EN + JA** | [`yang-netconf-restconf.yaml`](labs/yang-netconf/yang-netconf-restconf.yaml) |
| [BGP / iBGP / OSPF 冗長](labs/bgp-redundant/README.md) | Dual-homed eBGP, ISP core OSPF + iBGP, end-to-end PC traffic （**P ルータの役割**も解説） | **EN + JA** | [`bgp-ibgp-ospf-redundant.yaml`](labs/bgp-redundant/bgp-ibgp-ospf-redundant.yaml) |

## Common usage / 使い方（共通）

1. CML2 **Lab Manager → Import** で各ラボの YAML を取り込む / import the lab YAML  
2. 必要なノード定義とイメージがサーバにあることを確認する / confirm node definitions and images exist  
3. ラボを **Start** し、各 README の確認手順に従う / start nodes and follow that lab’s README  

Default credentials / 初期アカウント: `cisco` / `cisco`

### Which lab first? / どれから？

| If you want… / 目的 | Start here / こちら |
| --- | --- |
| Understand CE / PE / **P**, eBGP, iBGP, OSPF redundancy | [BGP lab](labs/bgp-redundant/README.md) — see **Why is there a P router?** |
| Learn YANG / NETCONF / RESTCONF APIs | [YANG lab](labs/yang-netconf/README.md) |

### Notes / 補足

- **YANG lab**: needs IOS-XE with YANG (`csr1000v` / `cat8000v` / IOL-XE). **`iosv` is not enough.**  
- **BGP lab**: uses `iosv` / `alpine` / `unmanaged_switch` (swap IOS image if needed).
