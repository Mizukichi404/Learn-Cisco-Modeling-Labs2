# CML2 BGP 学習ラボ（冗長 eBGP / iBGP / OSPF）

デュアルホームの顧客サイト 2 拠点と、OSPF + iBGP フルメッシュの ISP コアを組み合わせた学習用トポロジです。ユーザ PC 同士のエンドツーエンド通信と、リンク障害時の迂回を確認できます。

## インポート手順

1. CML2 の **Lab Manager → Import** を開く
2. [`bgp-ibgp-ospf-redundant.yaml`](./bgp-ibgp-ospf-redundant.yaml) を選択して取り込み
3. 全ノードを **Start** する（IOSv 5 台、Alpine 4 台、Unmanaged Switch 2 台）
4. 起動完了後、約 1〜2 分待って OSPF 隣接と BGP `Established` を確認する

ログインはすべて `cisco` / `cisco` です。

ノード定義は標準の `iosv` / `alpine` / `unmanaged_switch` です。CML に IOSv イメージが無い場合は、ラボ内の `iosv` を手元の IOS 系ノード（IOL / CSR1000v など）に差し替えてください。インタフェース名が違う場合は設定の修正が必要です。

設定を再生成する場合:

```bash
python3 labs/bgp-redundant/build_lab.py
```

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

- **CE-A / CE-B**: 各サイトのゲートウェイ。ISP の PE 2 台へ eBGP でデュアルホーム
- **PE1 / PE2**: ISP エッジ。eBGP で顧客プレフィックスを学習し、iBGP でコアへ配布（`next-hop-self`）
- **P**: ISP 中継。OSPF でループバック到達性を提供し、iBGP にも参加（P 経由転送時に顧客経路が必要）
- **SW-A / SW-B**: ユーザ LAN 用のアンマネージドスイッチ
- **PC-***: エンドユーザ。デフォルトゲートウェイは各 CE

冗長ポイント:

| 箇所 | 内容 |
| --- | --- |
| アクセス | 各 CE が PE1 と PE2 の両方と eBGP |
| ISP コア | PE1–PE2 直結と PE1–P–PE2 の三角 |
| iBGP | PE1 / PE2 / P のフルメッシュ（Loopback0 起点） |
| 経路選択 | Site-A は PE1 優先、Site-B は PE2 優先（`weight`） |

## アドレス設計

### ユーザ LAN

| サイト | セグメント | GW (CE) | PC |
| --- | --- | --- | --- |
| Site-A | 10.1.1.0/24 | 10.1.1.1 | PC-A1 `.10`, PC-A2 `.11` |
| Site-B | 10.2.2.0/24 | 10.2.2.1 | PC-B1 `.10`, PC-B2 `.11` |

### eBGP リンク（/30）

| リンク | ネットワーク | CE | PE |
| --- | --- | --- | --- |
| CE-A — PE1 | 192.168.13.0/30 | .1 | .2 |
| CE-A — PE2 | 192.168.14.0/30 | .1 | .2 |
| CE-B — PE1 | 192.168.23.0/30 | .1 | .2 |
| CE-B — PE2 | 192.168.24.0/30 | .1 | .2 |

### ISP コア（OSPF Area 0）

| リンク | ネットワーク | 側 A | 側 B |
| --- | --- | --- | --- |
| PE1 — P | 10.0.35.0/30 | PE1 `.1` | P `.2` |
| PE2 — P | 10.0.45.0/30 | PE2 `.1` | P `.2` |
| PE1 — PE2 | 10.0.34.0/30 | PE1 `.1` | PE2 `.2` |

| ルータ | Loopback0 | BGP ASN | 役割 |
| --- | --- | --- | --- |
| CE-A | 1.1.1.1/32 | 65001 | 顧客エッジ |
| CE-B | 2.2.2.2/32 | 65002 | 顧客エッジ |
| PE1 | 3.3.3.3/32 | 65000 | ISP PE |
| PE2 | 4.4.4.4/32 | 65000 | ISP PE |
| P | 5.5.5.5/32 | 65000 | ISP P（iBGP 含む） |

## プロトコル設計

1. **OSPF** は AS 65000 の IGP のみ。eBGP リンクは OSPF に入れない。`point-to-point` と短い hello（3 秒）で障害試験しやすくしてある。
2. **iBGP** は Loopback0 を `update-source` にし、IGP が迂回すれば TCP セッションも維持される。
3. **`next-hop-self`** により、iBGP で配る顧客経路の next-hop を PE のループバックにする（P が eBGP リンクへ到達できなくても転送できる）。
4. **eBGP** で各 CE が自サイト LAN を `network` で広告。PE は CE へ `default-originate` する。
5. CE の **`weight`** でプライマリ PE を寄せ、片系障害時はもう一方の eBGP に切り替わる。

学習時に見るべきポイント:

- eBGP の AD 20 が iBGP の AD 200 より優先されること
- `show ip bgp` の `Next Hop` が `next-hop-self` 後にループバックになること
- ユーザ PC は BGP を意識せず、デフォルトルートだけで対向 LAN に届くこと

個別コンフィグは [`configs/`](./configs/) を参照してください。

## エンドツーエンド確認

### 1. OSPF（ISP コア）

PE1 / PE2 / P で:

```text
show ip ospf neighbor
show ip route ospf
```

期待: 隣接が `FULL`。相手の Loopback（3.3.3.3 / 4.4.4.4 / 5.5.5.5）が OSPF 経路になる。

### 2. BGP

```text
show ip bgp summary
show ip bgp
show ip route bgp
```

期待:

- CE-A: 65000 向け 2 ネイバーが `Established`。`10.2.2.0/24` と default を学習
- PE1: iBGP 2 本 + eBGP 2 本が `Established`
- P: `10.1.1.0/24` と `10.2.2.0/24` を iBGP で保持（next-hop は PE のループバック）

### 3. ユーザ間通信

Alpine（PC-A1）のコンソール:

```text
ping -c 5 10.1.1.11
ping -c 5 10.2.2.10
ping -c 5 10.2.2.11
traceroute 10.2.2.10
```

PC-B1:

```text
ping -c 5 10.1.1.10
traceroute 10.1.1.10
```

同一 LAN の ping が通ればユーザ接続、対向サイトまで通れば eBGP + iBGP + OSPF の連携が成立しています。

CE 上でも確認できます:

```text
ping 10.2.2.10 source 10.1.1.1
traceroute 10.2.2.10 source 10.1.1.1
```

## 障害試験（冗長の確認）

試験中は PC-A1 から `ping 10.2.2.10` を流し続けておくと分かりやすいです。

### A. 顧客側のプライマリ eBGP 断

CE-A:

```text
configure terminal
interface GigabitEthernet0/0
 shutdown
end
show ip bgp summary
show ip route 10.2.2.0
```

期待: PE2 向け eBGP が残り、対向への ping が復旧する。

戻すときは `no shutdown`。

### B. PE1–PE2 直結断

PE1:

```text
configure terminal
interface GigabitEthernet0/1
 shutdown
end
show ip ospf neighbor
show ip route 4.4.4.4
```

期待: 4.4.4.4 が P 経由になる。iBGP（Loopback 起点）は維持。ユーザ通信は継続。

### C. P ルータ停止

P を Stop する、または両インタフェースを shutdown。

期待: PE1–PE2 直結と PE1–PE2 の iBGP が残るため、コアは片系で通信継続。

P が唯一の Route Reflector だとこの試験で iBGP が死にます。本ラボはフルメッシュにしてあるので P 障害に耐えます。

## 発展課題

- P を Route Reflector にし、PE1–PE2 の iBGP を外して差を観察する
- CE の `weight` をやめ `maximum-paths 2` で ECMP にする
- `route-map` で `local-preference` / `MED` / AS-path prepend を試す
- OSPF を Area 0 + Area 1 に分割し、PE だけ ABR にする
- MPLS + VPNv4 に拡張して PE 間をラベルスイッチにする
