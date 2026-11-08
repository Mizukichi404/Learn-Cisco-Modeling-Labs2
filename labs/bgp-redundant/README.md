# CML2 BGP Lab — Redundant eBGP / iBGP / OSPF

> **Languages / 言語**: This manual is bilingual.  
> English sections are marked **English**. Japanese sections are marked **日本語**.  
> このマニュアルは英語と日本語の併記です。英語は **English**、日本語は **日本語** です。

| Item / 項目 | Value / 値 |
| --- | --- |
| Import file / インポート | [`bgp-ibgp-ospf-redundant.yaml`](./bgp-ibgp-ospf-redundant.yaml) |
| Nodes / ノード | `iosv` ×5, `alpine` ×4, `unmanaged_switch` ×2 |
| Credentials / 認証 | `cisco` / `cisco` |
| Regenerate YAML / 再生成 | `python3 labs/bgp-redundant/build_lab.py` |

**Start here if you wondered “Why do we need a P router?”**  
**「P ルータはなぜ必要？」が気になった方は、まず下の初心者向け解説を読んでください。**

---

## English

### Beginner overview — the big picture

Imagine two company sites (Site-A and Site-B) that want to talk to each other through an ISP.

```text
  [Users at Site-A]          [ISP network]          [Users at Site-B]
   PC --- CE-A  =========  PE1 ---- P ---- PE2  =========  CE-B --- PC
                 eBGP         \          /         eBGP
                               \-- PE2--/   (also PE1--PE2 direct)
                                    OSPF + iBGP inside the ISP
```

Traffic story (simple):

1. A PC at Site-A sends a packet to Site-B’s LAN (`10.2.2.0/24`).
2. **CE-A** (customer gateway) forwards it to the ISP over **eBGP**.
3. An ISP **PE** (edge) accepts it, then the packet crosses the ISP **core**.
4. The far-side **PE** hands it to **CE-B**, which delivers it to the Site-B PC.

You do **not** need to memorize every address first. Remember three roles:

| Role | Full name | Who owns it? | Faces customers? | In this lab |
| --- | --- | --- | --- | --- |
| **CE** | Customer Edge | Customer | Yes (user LAN) | CE-A, CE-B |
| **PE** | Provider Edge | ISP | Yes (links to CE) | PE1, PE2 |
| **P** | Provider (core) | ISP | **No** | P |

- **CE** = the customer’s border router.  
- **PE** = the ISP’s border router (talks eBGP to customers, iBGP to the rest of the ISP).  
- **P** = an ISP core router that only forwards inside the ISP. It never connects to a customer.

### Why is there a P router?

Short answer: **connectivity between the two sites can work without P**, but then you cannot practice a realistic **ISP core** or **core-link failure**.

#### 1) Real ISPs separate edge and core

In production, customer-facing routers (PE) and pure transit routers (P) are different jobs:

- PE: many customer sessions, routing policy, filters, maybe VRFs later  
- P: high-speed forwarding between PEs; keep the design simple  

This lab’s **P** is that core role in miniature.

#### 2) P gives a second path inside the ISP (redundancy)

The ISP core is a **triangle**:

```text
        PE1 -------- PE2
          \          /
           \        /
              P
```

- Normal / preferred path can use the **PE1–PE2 direct** link.  
- If that link fails, OSPF still reaches the other PE **via P**.  
- Failover test **B** in this manual is exactly “why P exists.”

Without P, one PE–PE link cut would isolate the two PEs from each other (in a two-PE-only core).

#### 3) Why does P also run iBGP? (important)

This lab is **IP-only** (no MPLS).  
If a packet is forwarded **PE1 → P → PE2**, then **P must know the customer prefixes** (for example `10.2.2.0/24`). Otherwise P drops the packet (“no route”).

So P:

- runs **OSPF** → learns how to reach PE loopbacks  
- runs **iBGP** → learns customer routes from the PEs  
- uses PE **`next-hop-self`** → BGP next-hop becomes a PE loopback that OSPF already knows  

> **If we used MPLS**, a pure P often needs only the IGP (labels carry the rest).  
> That is a stretch goal. Here, **iBGP on P** replaces that lesson.

#### 4) What if we removed P?

| Design | What you can still learn | What you lose |
| --- | --- | --- |
| PE1–PE2 only (no P) | eBGP dual-home, basic iBGP | Core alternate path; “transit needs routes” |
| PE1–P–PE2 + PE1–PE2 (this lab) | All of the above + failover | Slightly more nodes/CPU |

**Bottom line:** P is not required for “Site-A pings Site-B” in the happy path.  
P is required for this lab’s **learning goals**: ISP core redundancy and understanding transit.

### Import steps

1. CML2 **Lab Manager → Import**
2. Select [`bgp-ibgp-ospf-redundant.yaml`](./bgp-ibgp-ospf-redundant.yaml)
3. **Start** all nodes (5× IOSv, 4× Alpine, 2× unmanaged switch)
4. Wait ~1–2 minutes for OSPF adjacencies and BGP `Established`

Login: `cisco` / `cisco`.

If `iosv` is missing, swap to another IOS image (IOL / CSR1000v, etc.) and fix interface names in configs if needed.

Regenerate:

```bash
python3 labs/bgp-redundant/build_lab.py
```

### Topology (detail)
## トポロジ

```text
 AS 65001 Site-A                         AS 65000 ISP Core                      AS 65002 Site-B
 10.1.1.0/24                             OSPF Area 0 + iBGP                     10.2.2.0/24

 PC-A1 10.1.1.10                         PE1 lo 3.3.3.3                          PC-B1 10.2.2.10
 PC-A2 10.1.1.11                           |  \                                  PC-B2 10.2.2.11
        \                                  |   \ OSPF                              /
         SW-A ---- CE-A ===== eBGP ===== PE1----P lo 5.5.5.5 ---- PE2 ===== eBGP ---- CE-B ---- SW-B
                   1.1.1.1    (dual-home)  |   / OSPF              4.4.4.4  (dual-home)   2.2.2.2
                                           |  /
                                         PE2
```

| Node | Role (one sentence) |
| --- | --- |
| CE-A / CE-B | Customer gateways; dual-homed eBGP to PE1 and PE2 |
| PE1 / PE2 | ISP edge; eBGP to customers, iBGP + `next-hop-self` into the core |
| **P** | ISP core transit; OSPF alternate path; iBGP so transit has customer routes |
| SW-A / SW-B | Unmanaged switches for user LANs |
| PC-\* | End users; default gateway = their CE |

Redundancy map:

| Place | What is redundant |
| --- | --- |
| Access | Each CE peers with **both** PE1 and PE2 (eBGP) |
| ISP core | PE1–PE2 direct **and** PE1–P–PE2 |
| iBGP | Full mesh PE1 / PE2 / P (sourced from Loopback0) |
| Path preference | Site-A prefers PE1, Site-B prefers PE2 (`weight`) |

### Addressing

#### User LANs

| Site | Subnet | GW (CE) | PCs |
| --- | --- | --- | --- |
| Site-A | 10.1.1.0/24 | 10.1.1.1 | PC-A1 `.10`, PC-A2 `.11` |
| Site-B | 10.2.2.0/24 | 10.2.2.1 | PC-B1 `.10`, PC-B2 `.11` |

#### eBGP links (/30)

| Link | Network | CE | PE |
| --- | --- | --- | --- |
| CE-A — PE1 | 192.168.13.0/30 | .1 | .2 |
| CE-A — PE2 | 192.168.14.0/30 | .1 | .2 |
| CE-B — PE1 | 192.168.23.0/30 | .1 | .2 |
| CE-B — PE2 | 192.168.24.0/30 | .1 | .2 |

#### ISP core (OSPF Area 0)

| Link | Network | Side A | Side B |
| --- | --- | --- | --- |
| PE1 — P | 10.0.35.0/30 | PE1 `.1` | P `.2` |
| PE2 — P | 10.0.45.0/30 | PE2 `.1` | P `.2` |
| PE1 — PE2 | 10.0.34.0/30 | PE1 `.1` | PE2 `.2` |

| Router | Loopback0 | ASN | Role |
| --- | --- | --- | --- |
| CE-A | 1.1.1.1/32 | 65001 | Customer edge |
| CE-B | 2.2.2.2/32 | 65002 | Customer edge |
| PE1 | 3.3.3.3/32 | 65000 | ISP PE |
| PE2 | 4.4.4.4/32 | 65000 | ISP PE |
| P | 5.5.5.5/32 | 65000 | ISP P (core) |

### Protocol design (beginner view)

1. **OSPF** only inside AS 65000 (ISP). eBGP links are **not** in OSPF.  
2. **iBGP** uses Loopback0 + `update-source`, so sessions survive link failover if IGP still reaches the loopback.  
3. **`next-hop-self`** on PEs: customer routes advertised into iBGP use the PE loopback as next-hop (reachable via OSPF, including through P).  
4. **eBGP**: each CE advertises its LAN; PEs send a default to CEs (`default-originate`).  
5. CE **`weight`** prefers one PE; if that link dies, the other eBGP path takes over.

Things to notice while learning:

- eBGP AD **20** beats iBGP AD **200**  
- After `next-hop-self`, `show ip bgp` next-hop becomes a PE loopback  
- User PCs only need a default route; they never run BGP  

Configs: [`configs/`](./configs/).

### End-to-end checks

#### 1) OSPF (ISP core)

On PE1 / PE2 / P:

```text
show ip ospf neighbor
show ip route ospf
```

Expect: `FULL` neighbors; peer loopbacks `3.3.3.3` / `4.4.4.4` / `5.5.5.5` via OSPF.

#### 2) BGP

```text
show ip bgp summary
show ip bgp
show ip route bgp
```

Expect:

- CE-A: two peers to 65000 `Established`; learns `10.2.2.0/24` and default  
- PE1: two iBGP + two eBGP `Established`  
- **P**: holds `10.1.1.0/24` and `10.2.2.0/24` via iBGP (next-hop = PE loopbacks)

#### 3) User traffic

On PC-A1:

```text
ping -c 5 10.1.1.11
ping -c 5 10.2.2.10
traceroute 10.2.2.10
```

On PC-B1:

```text
ping -c 5 10.1.1.10
traceroute 10.1.1.10
```

Same-LAN ping → user attachment OK. Cross-site ping → eBGP + iBGP + OSPF working together.

### Failover tests (this is where P shines)

Keep `ping 10.2.2.10` running from PC-A1.

#### A) Primary customer eBGP down

On CE-A shut the PE1-facing interface; traffic should move to PE2.

#### B) PE1–PE2 direct link down

```text
configure terminal
interface GigabitEthernet0/1
 shutdown
end
show ip route 4.4.4.4
```

Expect: `4.4.4.4` via **P**. iBGP (loopback-sourced) stays up. User traffic continues.  
**This test is the clearest demo of why P exists.**

#### C) Stop P

Expect: PE1–PE2 direct link + PE1–PE2 iBGP keep the core alive.  
(If P were the only route reflector, iBGP would break — this lab uses a full mesh on purpose.)

### Stretch goals

- Make P a route reflector; remove PE1–PE2 iBGP and compare  
- Replace CE `weight` with `maximum-paths 2`  
- Try `local-preference` / MED / AS-path prepend  
- Split OSPF areas  
- Add MPLS + VPNv4 so P can forward without customer IP routes  

---

## 日本語

### 初心者向け — 全体像

会社の拠点が 2 つ（Site-A と Site-B）あり、その間を ISP 経由でつなぐ、という話です。

```text
  [Site-A のユーザ]          [ISP 網]          [Site-B のユーザ]
   PC --- CE-A  =========  PE1 ---- P ---- PE2  =========  CE-B --- PC
                 eBGP         \          /         eBGP
                               \-- PE2--/   （PE1–PE2 直結もあり）
                                    ISP 内は OSPF + iBGP
```

パケットの流れ（ざっくり）:

1. Site-A の PC が Site-B の LAN（`10.2.2.0/24`）へ送る  
2. 顧客側の出口 **CE-A** が **eBGP** で ISP へ渡す  
3. ISP の端 **PE** が受け取り、ISP **コア** を通る  
4. 向こう側の **PE** が **CE-B** へ渡し、Site-B の PC に届く  

最初からアドレス表を全部覚える必要はありません。次の **3 役** だけ押さえてください。

| 役割 | 正式名のイメージ | 誰の装置？ | 顧客に接する？ | 本ラボ |
| --- | --- | --- | --- | --- |
| **CE** | Customer Edge（顧客エッジ） | 顧客 | する（ユーザ LAN） | CE-A, CE-B |
| **PE** | Provider Edge（ISP エッジ） | ISP | する（CE と接続） | PE1, PE2 |
| **P** | Provider（ISP コア） | ISP | **しない** | P |

- **CE** … お客さん側の関所  
- **PE** … ISP 側の関所（お客さんとは eBGP、ISP 内とは iBGP）  
- **P** … ISP の中継専用。お客さん回線は持たない  

### なぜ P ルータが必要なのか？

一言でいうと、**Site-A と Site-B が疎通するだけなら P 無しでも可能**です。  
ただしそれだと、**ISP コアの冗長**や **中継装置の役割**が学べません。

#### 1) 実際の ISP は「端」と「中」を分ける

本番ではだいたい次のように役割が分かれます。

- **PE**: 顧客セッション・ポリシー・フィルタ（将来は VRF など）  
- **P**: PE 同士をつなぐ高速な中継。設計を単純に保つ  

本ラボの **P** は、その「中継役」を小さくしたものです。

#### 2) P があると ISP 内に迂回路ができる（冗長）

ISP コアは次の **三角形** です。

```text
        PE1 -------- PE2
          \          /
           \        /
              P
```

- 普段は **PE1–PE2 直結** を使える  
- 直結が切れても、OSPF で **P 経由** に相手 PE へ届く  
- 後述の障害試験 **B** が、「P がいる意味」そのものです  

P が無いと、PE が 2 台だけのコアでは PE–PE リンク障害で互いに孤立しやすくなります。

#### 3) なぜ P でも iBGP を動かすのか（ここがポイント）

本ラボは **MPLS 無しの IP 転送**です。  
パケットが **PE1 → P → PE2** と流れるとき、**P も顧客プレフィックス**（例: `10.2.2.0/24`）を知っていないと転送できません。

そのため P は:

- **OSPF** … PE のループバックへどう行くかを知る  
- **iBGP** … 顧客経路を PE から学ぶ  
- PE の **`next-hop-self`** … BGP の next-hop が PE ループバックになり、OSPF で（P 経由でも）到達できる  

> **MPLS がある構成**では、P は IGP だけ持ってラベルで転送する、という形もあります。  
> それは発展課題です。本ラボでは **P の iBGP** がその代わりの学びになります。

#### 4) P を外したらどうなる？

| 構成 | 学べること | 失うこと |
| --- | --- | --- |
| PE1–PE2 のみ（P 無し） | eBGP デュアルホーム、基本的な iBGP | コア迂回路、「中継にも経路が要る」感覚 |
| PE1–P–PE2 + PE1–PE2（本ラボ） | 上記 + 障害時の迂回 | ノード数・CPU が少し増える |

**まとめ:** 平常時の ping 成功だけが目的なら P は必須ではありません。  
このラボの目的である **ISP コア冗長** と **中継の理解** のために P を置いています。

### インポート手順

1. CML2 の **Lab Manager → Import**  
2. [`bgp-ibgp-ospf-redundant.yaml`](./bgp-ibgp-ospf-redundant.yaml) を取り込む  
3. 全ノードを **Start**（IOSv 5 / Alpine 4 / Unmanaged Switch 2）  
4. 約 1〜2 分待ち、OSPF 隣接と BGP `Established` を確認  

ログインはすべて `cisco` / `cisco` です。

`iosv` が無い場合は IOL / CSR1000v などに差し替え、必要ならインタフェース名を修正してください。

再生成:

```bash
python3 labs/bgp-redundant/build_lab.py
```

### トポロジ（詳細）

（上図と同じ。役割の一文まとめ）

| ノード | 役割 |
| --- | --- |
| CE-A / CE-B | 顧客 GW。PE1 と PE2 の両方へ eBGP（デュアルホーム） |
| PE1 / PE2 | ISP エッジ。顧客とは eBGP、コアへは iBGP + `next-hop-self` |
| **P** | ISP 中継。OSPF の迂回路。顧客経路を持つための iBGP |
| SW-A / SW-B | ユーザ LAN 用スイッチ |
| PC-\* | エンドユーザ。DG は各 CE |

冗長の対応表:

| 箇所 | 内容 |
| --- | --- |
| アクセス | 各 CE が PE1 と PE2 の両方と eBGP |
| ISP コア | PE1–PE2 直結と PE1–P–PE2 の三角 |
| iBGP | PE1 / PE2 / P のフルメッシュ（Loopback0 起点） |
| 経路選択 | Site-A は PE1 優先、Site-B は PE2 優先（`weight`） |

### アドレス設計

#### ユーザ LAN

| サイト | セグメント | GW (CE) | PC |
| --- | --- | --- | --- |
| Site-A | 10.1.1.0/24 | 10.1.1.1 | PC-A1 `.10`, PC-A2 `.11` |
| Site-B | 10.2.2.0/24 | 10.2.2.1 | PC-B1 `.10`, PC-B2 `.11` |

#### eBGP リンク（/30）

| リンク | ネットワーク | CE | PE |
| --- | --- | --- | --- |
| CE-A — PE1 | 192.168.13.0/30 | .1 | .2 |
| CE-A — PE2 | 192.168.14.0/30 | .1 | .2 |
| CE-B — PE1 | 192.168.23.0/30 | .1 | .2 |
| CE-B — PE2 | 192.168.24.0/30 | .1 | .2 |

#### ISP コア（OSPF Area 0）

| リンク | ネットワーク | 側 A | 側 B |
| --- | --- | --- | --- |
| PE1 — P | 10.0.35.0/30 | PE1 `.1` | P `.2` |
| PE2 — P | 10.0.45.0/30 | PE2 `.1` | P `.2` |
| PE1 — PE2 | 10.0.34.0/30 | PE1 `.1` | PE2 `.2` |

| ルータ | Loopback0 | ASN | 役割 |
| --- | --- | --- | --- |
| CE-A | 1.1.1.1/32 | 65001 | 顧客エッジ |
| CE-B | 2.2.2.2/32 | 65002 | 顧客エッジ |
| PE1 | 3.3.3.3/32 | 65000 | ISP PE |
| PE2 | 4.4.4.4/32 | 65000 | ISP PE |
| P | 5.5.5.5/32 | 65000 | ISP P（コア） |

### プロトコル設計（初心者向け）

1. **OSPF** は AS 65000（ISP）の中だけ。eBGP リンクは OSPF に入れない  
2. **iBGP** は Loopback0 を `update-source` にし、IGP が届けばセッションを維持  
3. PE の **`next-hop-self`** で、iBGP 上の顧客経路の next-hop を PE ループバックにする  
4. **eBGP** で CE が自 LAN を広告。PE は CE へ `default-originate`  
5. CE の **`weight`** で優先 PE を寄せ、片系障害時はもう一方へ切替  

学習時の観察ポイント:

- eBGP の AD 20 が iBGP の AD 200 より優先されること  
- `next-hop-self` 後、`show ip bgp` の Next Hop がループバックになること  
- ユーザ PC は BGP を知らず、デフォルトルートだけで対向に届くこと  

個別コンフィグは [`configs/`](./configs/) を参照。

### エンドツーエンド確認

#### 1) OSPF（ISP コア）

PE1 / PE2 / P で:

```text
show ip ospf neighbor
show ip route ospf
```

期待: 隣接 `FULL`。相手 Loopback（3.3.3.3 / 4.4.4.4 / 5.5.5.5）が OSPF 経路。

#### 2) BGP

```text
show ip bgp summary
show ip bgp
show ip route bgp
```

期待:

- CE-A: 65000 向け 2 ネイバーが `Established`。`10.2.2.0/24` と default を学習  
- PE1: iBGP 2 + eBGP 2 が `Established`  
- **P**: `10.1.1.0/24` と `10.2.2.0/24` を iBGP で保持（next-hop は PE ループバック）

#### 3) ユーザ間通信

PC-A1:

```text
ping -c 5 10.1.1.11
ping -c 5 10.2.2.10
traceroute 10.2.2.10
```

PC-B1:

```text
ping -c 5 10.1.1.10
traceroute 10.1.1.10
```

同一 LAN の ping → ユーザ接続 OK。対向サイト → eBGP + iBGP + OSPF の連携 OK。

### 障害試験（ここで P の意味が体感できる）

PC-A1 から `ping 10.2.2.10` を流し続けると分かりやすいです。

#### A) 顧客側プライマリ eBGP 断

CE-A で PE1 向けインタフェースを shutdown。PE2 経由へ切替わることを確認。

#### B) PE1–PE2 直結断

```text
configure terminal
interface GigabitEthernet0/1
 shutdown
end
show ip route 4.4.4.4
```

期待: `4.4.4.4` が **P 経由** になる。iBGP（Loopback 起点）は維持。ユーザ通信は継続。  
**「P が必要な理由」が一番よく分かる試験です。**

#### C) P ルータ停止

期待: PE1–PE2 直結と PE1–PE2 の iBGP が残るため、コアは片系で継続。  
（P だけを Route Reflector にしていると、この試験で iBGP が死にます。本ラボはフルメッシュなので耐えます。）

### 発展課題

- P を Route Reflector にし、PE1–PE2 の iBGP を外して差を観察する  
- CE の `weight` をやめ `maximum-paths 2` で ECMP にする  
- `local-preference` / MED / AS-path prepend を試す  
- OSPF を Area 分割する  
- MPLS + VPNv4 に拡張し、P が顧客 IP 経路を持たなくても転送できる形を見る  
