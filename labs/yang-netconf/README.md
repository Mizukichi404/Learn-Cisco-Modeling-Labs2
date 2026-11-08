# CML2 YANG Lab — NETCONF / RESTCONF

> **Languages / 言語**: This manual is bilingual.  
> English sections are marked **English**. Japanese sections are marked **日本語**.  
> このマニュアルは英語と日本語の併記です。英語は **English**、日本語は **日本語** です。

| Item / 項目 | Value / 値 |
| --- | --- |
| Import file / インポート | [`yang-netconf-restconf.yaml`](./yang-netconf-restconf.yaml) |
| Nodes / ノード | `csr1000v` ×2, `alpine` ×1, `unmanaged_switch` ×1 |
| Credentials / 認証 | `cisco` / `cisco` |
| Client scripts / クライアント | [`scripts/`](./scripts/) |
| Regenerate YAML / 再生成 | `python3 labs/yang-netconf/build_lab.py` |

---

## English

### Beginner overview — the big picture

This lab is **not** an ISP CE/PE/P design. There is **no P router** here.

| Lab | What it teaches | Core devices |
| --- | --- | --- |
| **This YANG lab** | How to manage routers with YANG APIs | R1, R2, MGMT-PC |
| [BGP redundant lab](../bgp-redundant/README.md) | CE / PE / **P**, eBGP, iBGP, OSPF failover | CE, PE1, PE2, **P**, PCs |

If you came here wondering **“Why do we need a P router?”**, that question belongs to the BGP lab — see its section **Why is there a P router?**

What each box does in *this* lab:

```text
  You (operator)
       |
       v
   MGMT-PC  ----(mgmt LAN)----  R1  ----(OSPF link)----  R2
   curl /                      APIs on                 APIs on
   ncclient                    172.16.0.1              172.16.0.2
```

| Device | Beginner meaning |
| --- | --- |
| **R1 / R2** | Two routers you will manage. They run OSPF between them so there is “real” config and state to read. |
| **SW-MGMT** | A simple switch so MGMT-PC, R1, and R2 share one management LAN. |
| **MGMT-PC** | Your client PC inside the lab (Alpine). From here you call NETCONF/RESTCONF. |

Think of it as: **CLI practice → replace parts of CLI with YANG-based tools.**

### What you will learn

This lab builds a small CML2 environment for **model-driven network management**:

1. **YANG** — data models that describe device configuration and operational state  
2. **NETCONF** — XML over SSH (TCP/830) using `<get-config>`, `<edit-config>`, `<get>`  
3. **RESTCONF** — HTTPS JSON/XML API mapped from the same YANG models  

You configure two IOS-XE routers (`csr1000v`), enable NETCONF/RESTCONF, form OSPF between them, then read and change configuration from a management PC (or your laptop) using curl / Python `ncclient`.

### Import steps

1. In CML2 open **Lab Manager → Import**
2. Select [`yang-netconf-restconf.yaml`](./yang-netconf-restconf.yaml)
3. Confirm node definitions exist: `csr1000v`, `alpine`, `unmanaged_switch`
4. **Start** all nodes (CSR1000v needs more RAM/CPU; first boot can take several minutes)
5. Wait until OSPF is `FULL` and YANG processes are up (see verification below)

If your CML server has no `csr1000v` image, replace both routers with another IOS-XE node (`cat8000v` / `c8000v` / IOL-XE). Interface names may differ — adjust configs in [`configs/`](./configs/) and rebuild with `build_lab.py` if needed.

`iosv` is **not** suitable for this lab (weak / missing NETCONF·RESTCONF·YANG support).

### Topology

```text
                 MGMT LAN 172.16.0.0/24
  +-----------+      +----------+      +-----------+
  |    R1     |------| SW-MGMT  |------|    R2     |
  | 172.16.0.1|      |          |      | 172.16.0.2|
  | lo 1.1.1.1|      +----+-----+      | lo 2.2.2.2|
  +-----+-----+           |            +-----+-----+
        |                 |                  |
        |            MGMT-PC                 |
        |          172.16.0.10               |
        |                                    |
        +-------- Gi2 10.0.12.0/30 ----------+
                     OSPF Area 0
```

| Role | Node | Notes |
| --- | --- | --- |
| IOS-XE PE/lab router | R1, R2 | NETCONF + RESTCONF + SSH + OSPF |
| L2 hub | SW-MGMT | Connects management interfaces and MGMT-PC |
| Client | MGMT-PC (Alpine) | Reach `172.16.0.1` / `.2` for API calls |

### Addressing

| Device | Interface | Address | Purpose |
| --- | --- | --- | --- |
| R1 | Loopback0 | 1.1.1.1/32 | Router-ID / YANG edit target |
| R1 | GigabitEthernet1 | 172.16.0.1/24 | Management + API |
| R1 | GigabitEthernet2 | 10.0.12.1/30 | OSPF to R2 |
| R2 | Loopback0 | 2.2.2.2/32 | Router-ID / YANG edit target |
| R2 | GigabitEthernet1 | 172.16.0.2/24 | Management + API |
| R2 | GigabitEthernet2 | 10.0.12.2/30 | OSPF to R1 |
| MGMT-PC | eth0 | 172.16.0.10/24 | Client workstation |

| Protocol | Port | Path / notes |
| --- | --- | --- |
| SSH | 22 | CLI |
| NETCONF | 830 | SSH subsystem `netconf` |
| RESTCONF | 443 (HTTPS) | `/restconf/...` (HTTP 80 also enabled for lab simplicity) |

### Concepts (short)

| Term | Meaning |
| --- | --- |
| **YANG** | Language/schema for configuration and state. Devices advertise modules as capabilities. |
| **NETCONF** | Standard RPC protocol. Best for transactional config (`candidate`/`running`, locks). |
| **RESTCONF** | HTTP mapping of YANG. Easy with `curl` and browsers/tools; uses media type `application/yang-data+json`. |
| **Native model** | Vendor tree such as `Cisco-IOS-XE-native` (mirrors much of IOS CLI structure). |
| **OpenConfig / IETF** | Industry/standard models; support varies by image and version. |

Learning path in this lab: enable services → list capabilities → `get-config` → RESTCONF GET → `edit-config` / PATCH → confirm on CLI.

### Device feature checklist (already in day-0 config)

On R1 / R2 the bootstrap config enables:

- local AAA user `cisco`
- RSA key + SSHv2
- `netconf-yang` and `restconf`
- `ip http secure-server` / `ip http server`
- OSPF Area 0 on the R1–R2 link and loopbacks

See [`configs/R1.txt`](./configs/R1.txt) and [`configs/R2.txt`](./configs/R2.txt).

### Verification on the routers

```text
show ip interface brief
show ip ospf neighbor
show ip route ospf
show netconf-yang status
show platform software yang-management process
show restconf
show run | section netconf|restconf|http
```

Expected:

- OSPF neighbor `FULL` on GigabitEthernet2
- Opposite loopback learned via OSPF (`1.1.1.1` or `2.2.2.2`)
- NETCONF-YANG status enabled / datastores ready
- YANG processes (confd, nginx, etc. — names vary by XE version) running

From MGMT-PC (or any host on 172.16.0.0/24):

```text
ping -c 3 172.16.0.1
ping -c 3 172.16.0.2
```

### Lab exercises

#### 1) Confirm NETCONF capabilities

From a host with Python + `ncclient` (MGMT-PC if packages are installed, or your PC via CML breakout / external connector):

```bash
pip install ncclient
python3 scripts/netconf_get_config.py --host 172.16.0.1 --filter interfaces
```

Watch the capability URIs — they are the YANG modules the device supports.

#### 2) RESTCONF read with curl

```bash
export R1=172.16.0.1 AUTH=cisco:cisco
curl -k -u "$AUTH" -H "Accept: application/yang-data+json" \
  "https://$R1/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback=0"
```

Or run the helper:

```bash
chmod +x scripts/restconf_examples.sh
./scripts/restconf_examples.sh
```

#### 3) Change Loopback description via NETCONF

```bash
python3 scripts/netconf_edit_loopback.py \
  --host 172.16.0.1 \
  --description "learned-via-NETCONF"
```

On R1 CLI:

```text
show interfaces Loopback0 description
show run interface Loopback0
```

#### 4) Change the same leaf via RESTCONF PATCH

```bash
curl -k -u cisco:cisco -X PATCH \
  -H "Accept: application/yang-data+json" \
  -H "Content-Type: application/yang-data+json" \
  -d '{"Cisco-IOS-XE-native:Loopback":[{"name":0,"description":"learned-via-RESTCONF"}]}' \
  "https://172.16.0.1/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback=0"
```

#### 5) Operational state (not only config)

Try oper models (module names depend on XE version), for example:

```bash
curl -k -u cisco:cisco -H "Accept: application/yang-data+json" \
  "https://172.16.0.1/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
```

Compare with `show ip interface brief` — same truth, different encoding.

### Troubleshooting

| Symptom | What to check |
| --- | --- |
| NETCONF connection refused | `show netconf-yang status`; wait for yang-management processes; confirm TCP/830 |
| RESTCONF HTTP 401 / empty | User privilege 15, `ip http authentication local`, correct `cisco:cisco` |
| RESTCONF 404 on a path | Module/path differs by image — start from `/restconf/` or `/restconf/data/Cisco-IOS-XE-native:native` |
| CSR boot OOM / stuck | Raise RAM to 4096+ MB in CML node settings |
| No `csr1000v` | Swap to another IOS-XE node definition; keep NETCONF/RESTCONF commands |

### Stretch goals

- Use `candidate` datastore + `<commit>` if the image advertises `:candidate`
- Add OpenConfig interface model reads if capabilities include `openconfig-interfaces`
- Point Cisco YANG Suite / Postman at R1 and browse modules graphically
- Add a third router and push OSPF network statements only via NETCONF

---

## 日本語

### 初心者向け — 全体像

このラボは ISP の CE / PE / **P** 構成ではありません。**P ルータは出てきません。**

| ラボ | 学ぶこと | 主な装置 |
| --- | --- | --- |
| **この YANG ラボ** | YANG API でルータを操作する方法 | R1, R2, MGMT-PC |
| [BGP 冗長ラボ](../bgp-redundant/README.md) | CE / PE / **P**、eBGP、iBGP、OSPF 障害迂回 | CE, PE1, PE2, **P**, PC |

**「P ルータはなぜ必要？」** が知りたい場合は、BGP ラボの **「なぜ P ルータが必要なのか？」** を読んでください。

このラボの各装置の意味:

```text
  あなた（操作する人）
       |
       v
   MGMT-PC  ----(管理 LAN)----  R1  ----(OSPF リンク)----  R2
   curl /                     API は                  API は
   ncclient                   172.16.0.1              172.16.0.2
```

| 装置 | 初心者向けの意味 |
| --- | --- |
| **R1 / R2** | 管理対象のルータ 2 台。OSPF を張って「読む・変える」対象の設定と状態を作る |
| **SW-MGMT** | MGMT-PC と R1 / R2 を同じ管理 LAN につなぐだけのスイッチ |
| **MGMT-PC** | ラボ内の操作用 PC（Alpine）。ここから NETCONF / RESTCONF を叩く |

イメージは **「CLI でやっていた操作の一部を、YANG ベースの道具に置き換える」** です。

### このラボで学ぶこと

CML2 上に **モデル駆動型ネットワーク管理** の小さな環境を作ります。

1. **YANG** — 装置の設定・状態を表現するデータモデル  
2. **NETCONF** — SSH 上の XML（TCP/830）。`<get-config>` / `<edit-config>` / `<get>` など  
3. **RESTCONF** — 同じ YANG を HTTPS の JSON/XML API にしたもの  

IOS-XE（`csr1000v`）を 2 台用意し、NETCONF/RESTCONF を有効化、OSPF を張り、管理 PC（または手元 PC）から curl / Python `ncclient` で設定の取得・変更を行います。

### インポート手順

1. CML2 の **Lab Manager → Import** を開く  
2. [`yang-netconf-restconf.yaml`](./yang-netconf-restconf.yaml) を取り込む  
3. ノード定義 `csr1000v` / `alpine` / `unmanaged_switch` とイメージがあることを確認  
4. 全ノードを **Start**（CSR1000v はメモリ多め。初回起動は数分かかることがある）  
5. OSPF が `FULL`、YANG プロセスが起動するまで待つ（下記の確認コマンド参照）

サーバに `csr1000v` が無い場合は、同じ IOS-XE 系（`cat8000v` / `c8000v` / IOL-XE など）に差し替えてください。インタフェース名が違う場合は [`configs/`](./configs/) を直し、必要なら `build_lab.py` で YAML を再生成します。

`iosv` はこのラボ向きではありません（NETCONF / RESTCONF / YANG が弱い、または無いため）。

### トポロジ

```text
                 管理 LAN 172.16.0.0/24
  +-----------+      +----------+      +-----------+
  |    R1     |------| SW-MGMT  |------|    R2     |
  | 172.16.0.1|      |          |      | 172.16.0.2|
  | lo 1.1.1.1|      +----+-----+      | lo 2.2.2.2|
  +-----+-----+           |            +-----+-----+
        |                 |                  |
        |            MGMT-PC                 |
        |          172.16.0.10               |
        |                                    |
        +-------- Gi2 10.0.12.0/30 ----------+
                     OSPF Area 0
```

| 役割 | ノード | 内容 |
| --- | --- | --- |
| IOS-XE ルータ | R1, R2 | NETCONF + RESTCONF + SSH + OSPF |
| L2 ハブ | SW-MGMT | 管理インタフェースと MGMT-PC を接続 |
| クライアント | MGMT-PC (Alpine) | `172.16.0.1` / `.2` へ API 実行 |

### アドレス設計

| 装置 | インタフェース | アドレス | 用途 |
| --- | --- | --- | --- |
| R1 | Loopback0 | 1.1.1.1/32 | Router-ID / YANG 変更対象 |
| R1 | GigabitEthernet1 | 172.16.0.1/24 | 管理・API |
| R1 | GigabitEthernet2 | 10.0.12.1/30 | R2 向け OSPF |
| R2 | Loopback0 | 2.2.2.2/32 | Router-ID / YANG 変更対象 |
| R2 | GigabitEthernet1 | 172.16.0.2/24 | 管理・API |
| R2 | GigabitEthernet2 | 10.0.12.2/30 | R1 向け OSPF |
| MGMT-PC | eth0 | 172.16.0.10/24 | 操作用ホスト |

| プロトコル | ポート | メモ |
| --- | --- | --- |
| SSH | 22 | CLI |
| NETCONF | 830 | SSH サブシステム `netconf` |
| RESTCONF | 443 (HTTPS) | `/restconf/...`（学習用に HTTP 80 も有効） |

### 概念（短く）

| 用語 | 意味 |
| --- | --- |
| **YANG** | 設定・状態のスキーマ。装置は capability としてモジュールを広告する |
| **NETCONF** | 標準の RPC。トランザクション（`candidate` / lock）向き |
| **RESTCONF** | YANG の HTTP 写像。`curl` で扱いやすい。メディアタイプは `application/yang-data+json` |
| **Native モデル** | `Cisco-IOS-XE-native` など、CLI に近いベンダーツリー |
| **OpenConfig / IETF** | 業界・標準モデル。イメージと版で対応差あり |

進め方: サービス有効化 → capability 確認 → `get-config` → RESTCONF GET → `edit-config` / PATCH → CLI で確認。

### day-0 で入っている機能

R1 / R2 の初期設定には次が含まれます。

- ローカルユーザ `cisco`（AAA）
- RSA 鍵 + SSHv2
- `netconf-yang` と `restconf`
- `ip http secure-server` / `ip http server`
- R1–R2 リンクとループバックの OSPF Area 0

詳細は [`configs/R1.txt`](./configs/R1.txt) / [`configs/R2.txt`](./configs/R2.txt)。

### ルータ上の確認

```text
show ip interface brief
show ip ospf neighbor
show ip route ospf
show netconf-yang status
show platform software yang-management process
show restconf
show run | section netconf|restconf|http
```

期待値:

- GigabitEthernet2 で OSPF 隣接が `FULL`
- 対向ループバックが OSPF 経路になる
- NETCONF-YANG が有効
- YANG 関連プロセスが動作（版により名前は異なる）

MGMT-PC（または同一セグメントのホスト）から:

```text
ping -c 3 172.16.0.1
ping -c 3 172.16.0.2
```

### 演習

#### 1) NETCONF capability の確認

Python + `ncclient` があるホストで（MGMT-PC、または CML の breakout / external connector 経由の手元 PC）:

```bash
pip install ncclient
python3 scripts/netconf_get_config.py --host 172.16.0.1 --filter interfaces
```

表示される capability URI が、その装置が持つ YANG モジュールです。

#### 2) curl で RESTCONF 読み取り

```bash
export R1=172.16.0.1 AUTH=cisco:cisco
curl -k -u "$AUTH" -H "Accept: application/yang-data+json" \
  "https://$R1/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback=0"
```

ヘルパーでも可:

```bash
chmod +x scripts/restconf_examples.sh
./scripts/restconf_examples.sh
```

#### 3) NETCONF で Loopback の description を変更

```bash
python3 scripts/netconf_edit_loopback.py \
  --host 172.16.0.1 \
  --description "learned-via-NETCONF"
```

R1 の CLI:

```text
show interfaces Loopback0 description
show run interface Loopback0
```

#### 4) RESTCONF PATCH でも同じリーフを変更

```bash
curl -k -u cisco:cisco -X PATCH \
  -H "Accept: application/yang-data+json" \
  -H "Content-Type: application/yang-data+json" \
  -d '{"Cisco-IOS-XE-native:Loopback":[{"name":0,"description":"learned-via-RESTCONF"}]}' \
  "https://172.16.0.1/restconf/data/Cisco-IOS-XE-native:native/interface/Loopback=0"
```

#### 5) 運用状態（設定だけではない）の取得

版によってモジュール名は違いますが、例:

```bash
curl -k -u cisco:cisco -H "Accept: application/yang-data+json" \
  "https://172.16.0.1/restconf/data/Cisco-IOS-XE-interfaces-oper:interfaces"
```

`show ip interface brief` と同じ情報を、別の符号化で見ている、という理解がポイントです。

### トラブルシュート

| 症状 | 確認すること |
| --- | --- |
| NETCONF が接続拒否 | `show netconf-yang status`、yang プロセス待ち、TCP/830 |
| RESTCONF 401 / 空応答 | 特権 15、`ip http authentication local`、ユーザ `cisco:cisco` |
| パスで 404 | イメージ差。`/restconf/` や `.../Cisco-IOS-XE-native:native` から辿る |
| CSR が起動しない / OOM | ノード RAM を 4096 MB 以上に |
| `csr1000v` が無い | 他の IOS-XE 定義へ置換（NETCONF/RESTCONF コマンドは維持） |

### 発展課題

- capability に `:candidate` があれば `candidate` + `<commit>` を試す  
- `openconfig-interfaces` があれば OpenConfig でインタフェースを読む  
- Cisco YANG Suite や Postman を R1 に向け、モジュールを GUI で眺める  
- 3 台目を足し、OSPF の `network` 文だけを NETCONF で投入する  

---

## File map / ファイル構成

| Path | English | 日本語 |
| --- | --- | --- |
| `yang-netconf-restconf.yaml` | CML2 import topology | CML2 取り込み用トポロジ |
| `build_lab.py` | Regenerates YAML + `configs/` | YAML と `configs/` を再生成 |
| `configs/*.txt` | Per-node reference configs | ノード別参照コンフィグ |
| `scripts/netconf_*.py` | NETCONF client examples | NETCONF クライアント例 |
| `scripts/restconf_examples.sh` | RESTCONF curl walkthrough | RESTCONF の curl 手順 |
