#!/usr/bin/env python3
"""把交割单配对成「已清仓」交易，按持有期分组统计。只用标准库，只处理做多。

输入：标准格式的成交 CSV（UTF-8），表头至少包含 date,code,side,qty,price
      可选列：time,name,fee,plan_id
      date 写 YYYY-MM-DD；side 写 买/卖（也认 B/S、buy/sell）；qty 为正数；
      fee 为这一笔成交的全部费用（佣金 + 印花税 + 过户费等），没有就当 0。

配对口径（运行时会打印出来，先给用户确认）：
  cycle（默认）：同一只标的从 0 建仓到重新清仓为 0，算一笔已清仓交易。
                 持有天数 = 最后一次卖出日 − 第一次买入日（自然日）；盈亏 = 这一轮所有卖出所得 − 买入成本 − 费用。
  lot         ：先进先出，每一次卖出按最早的买入批次配对，按「买入日 × 卖出日」合并成一笔。

用法：
  python3 pair_trades.py trades.csv
  python3 pair_trades.py trades.csv --mode lot
  python3 pair_trades.py trades.csv --groups 7,60           # 分组边界（天），默认 3,7,30
  python3 pair_trades.py trades.csv --out closed.csv        # 另存已清仓明细

输出：Markdown（打印到屏幕），包括口径、分组统计、亏损最大的 10 笔、对不上的记录、未清仓持仓。
"""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date

BUY = {"买", "买入", "b", "buy", "证券买入"}
SELL = {"卖", "卖出", "s", "sell", "证券卖出"}
EPS = 1e-9


def parse_date(s):
    s = s.strip().replace("/", "-").replace(".", "-")
    if len(s) == 8 and s.isdigit():
        s = f"{s[:4]}-{s[4:6]}-{s[6:]}"
    y, m, d = (int(x) for x in s.split("-")[:3])
    return date(y, m, d)


def num(s, default=0.0):
    s = (s or "").strip().replace(",", "")
    return float(s) if s else default


def load(path):
    rows, bad = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        missing = {"date", "code", "side", "qty", "price"} - set(reader.fieldnames or [])
        if missing:
            sys.exit(f"缺少必需列：{', '.join(sorted(missing))}。先把券商导出的列映射成标准表头。")
        for i, r in enumerate(reader, start=2):
            try:
                side_raw = (r.get("side") or "").strip().lower()
                side = "买" if side_raw in BUY else "卖" if side_raw in SELL else None
                if side is None:
                    raise ValueError(f"方向无法识别：{r.get('side')}")
                qty = abs(num(r.get("qty")))
                if qty <= 0:
                    raise ValueError("数量为 0")
                rows.append({
                    "line": i,
                    "date": parse_date(r["date"]),
                    "time": (r.get("time") or "").strip(),
                    "code": r["code"].strip(),
                    "name": (r.get("name") or "").strip(),
                    "side": side,
                    "qty": qty,
                    "price": num(r.get("price")),
                    "fee": abs(num(r.get("fee"))),
                })
            except Exception as e:  # 拿不准的记录单独列出，不猜
                bad.append((i, str(e)))
    rows.sort(key=lambda x: (x["date"], x["time"], x["line"]))
    return rows, bad


def pair_cycle(rows):
    closed, unmatched, open_pos = [], [], []
    state = {}
    for r in rows:
        st = state.get(r["code"])
        if r["side"] == "买":
            if st is None:
                st = {"code": r["code"], "name": r["name"], "start": r["date"], "pos": 0.0,
                      "cost": 0.0, "proceeds": 0.0, "fills": 0}
                state[r["code"]] = st
            st["pos"] += r["qty"]
            st["cost"] += r["qty"] * r["price"] + r["fee"]
            st["fills"] += 1
            st["name"] = st["name"] or r["name"]
        else:
            if st is None or st["pos"] <= EPS:
                unmatched.append((r, "卖出前没有对应的买入（可能是导出区间之前买的）"))
                continue
            q = min(r["qty"], st["pos"])
            if r["qty"] - q > EPS:
                unmatched.append((r, f"卖出数量多出 {r['qty'] - q:g}，多出部分没有对应买入"))
            fee = r["fee"] * (q / r["qty"])
            st["pos"] -= q
            st["proceeds"] += q * r["price"] - fee
            st["fills"] += 1
            if st["pos"] <= EPS:
                pnl = st["proceeds"] - st["cost"]
                closed.append({
                    "code": st["code"], "name": st["name"], "buy_date": st["start"],
                    "sell_date": r["date"], "days": (r["date"] - st["start"]).days,
                    "pnl": pnl, "ret": pnl / st["cost"] if st["cost"] else 0.0, "fills": st["fills"],
                })
                del state[r["code"]]
    for st in state.values():
        open_pos.append((st["code"], st["name"], st["pos"], st["start"]))
    return closed, unmatched, open_pos


def pair_lot(rows):
    lots = defaultdict(list)  # code -> [[date, qty_left, price, fee_per_share, name]]
    merged = defaultdict(lambda: {"qty": 0.0, "cost": 0.0, "proceeds": 0.0})
    names, unmatched = {}, []
    for r in rows:
        names.setdefault(r["code"], r["name"])
        if r["side"] == "买":
            lots[r["code"]].append([r["date"], r["qty"], r["price"], r["fee"] / r["qty"]])
            continue
        left = r["qty"]
        sell_fee_ps = r["fee"] / r["qty"]
        q_lots = lots[r["code"]]
        while left > EPS and q_lots:
            lot = q_lots[0]
            q = min(left, lot[1])
            key = (r["code"], lot[0], r["date"])
            m = merged[key]
            m["qty"] += q
            m["cost"] += q * (lot[2] + lot[3])
            m["proceeds"] += q * (r["price"] - sell_fee_ps)
            lot[1] -= q
            left -= q
            if lot[1] <= EPS:
                q_lots.pop(0)
        if left > EPS:
            unmatched.append((r, f"卖出数量多出 {left:g}，没有对应买入"))
    closed = []
    for (code, bd, sd), m in merged.items():
        pnl = m["proceeds"] - m["cost"]
        closed.append({"code": code, "name": names.get(code, ""), "buy_date": bd, "sell_date": sd,
                       "days": (sd - bd).days, "pnl": pnl,
                       "ret": pnl / m["cost"] if m["cost"] else 0.0, "fills": 2})
    open_pos = [(c, names.get(c, ""), sum(l[1] for l in ls), ls[0][0]) for c, ls in lots.items() if ls]
    return closed, unmatched, open_pos


def group_label(days, bounds):
    lo = 0
    for b in bounds:
        if days <= b:
            return f"{lo}–{b} 天" if lo else f"≤ {b} 天"
        lo = b + 1
    return f"> {bounds[-1]} 天"


def money(x):
    return f"{x:,.2f}"


def main():
    p = argparse.ArgumentParser(description="交割单配对 + 按持有期分组")
    p.add_argument("csv")
    p.add_argument("--mode", choices=["cycle", "lot"], default="cycle")
    p.add_argument("--groups", default="3,7,30", help="分组边界（天），逗号分隔")
    p.add_argument("--out", help="另存已清仓明细 CSV")
    a = p.parse_args()

    bounds = sorted(int(x) for x in a.groups.split(",") if x.strip())
    rows, bad = load(a.csv)
    closed, unmatched, open_pos = (pair_cycle if a.mode == "cycle" else pair_lot)(rows)

    print("## 交割单配对结果\n")
    if a.mode == "cycle":
        print("- 配对口径：cycle——同一只标的从建仓到清仓为 0 算一笔；持有天数 = 最后卖出日 − 第一次买入日（自然日）")
    else:
        print("- 配对口径：lot——先进先出，按「买入日 × 卖出日」合并成一笔")
    print(f"- 读入成交 {len(rows)} 条；已清仓 {len(closed)} 笔；对不上的 {len(unmatched)} 条；无法解析 {len(bad)} 条；未清仓 {len(open_pos)} 只")
    print("- 盈亏已扣除 CSV 里填写的费用；未清仓的不计入\n")

    groups = defaultdict(list)
    for c in closed:
        groups[group_label(c["days"], bounds)].append(c)
    order = [group_label(b, bounds) for b in bounds] + [f"> {bounds[-1]} 天"]

    print("### 按持有期分组\n")
    print("| 持有期 | 笔数 | 已清仓合计盈亏 | 胜率 | 平均盈利 | 平均亏损 | 盈亏比 |")
    print("|:---|---:|---:|---:|---:|---:|---:|")
    for g in order:
        cs = groups.get(g, [])
        if not cs:
            print(f"| {g} | 0 | — | — | — | — | — |")
            continue
        wins = [c["pnl"] for c in cs if c["pnl"] > 0]
        losses = [c["pnl"] for c in cs if c["pnl"] <= 0]
        aw = sum(wins) / len(wins) if wins else 0.0
        al = sum(losses) / len(losses) if losses else 0.0
        ratio = f"{aw / abs(al):.2f}" if wins and losses and al != 0 else "—"
        flag = "（样本少）" if len(cs) < 10 else ""
        print(f"| {g}{flag} | {len(cs)} | {money(sum(c['pnl'] for c in cs))} | {len(wins) / len(cs) * 100:.1f}% "
              f"| {money(aw) if wins else '—'} | {money(al) if losses else '—'} | {ratio} |")
    total = sum(c["pnl"] for c in closed)
    print(f"| 全部 | {len(closed)} | {money(total)} | "
          f"{(sum(1 for c in closed if c['pnl'] > 0) / len(closed) * 100) if closed else 0:.1f}% | | | |\n")

    print("### 亏损最大的 10 笔\n")
    print("| 标的 | 买入日 | 卖出日 | 持有天数 | 所在组 | 盈亏 | 收益率 |")
    print("|:---|:---|:---|---:|:---|---:|---:|")
    for c in sorted(closed, key=lambda c: c["pnl"])[:10]:
        if c["pnl"] >= 0:
            break
        label = f"{c['code']} {c['name']}".strip()
        print(f"| {label} | {c['buy_date']} | {c['sell_date']} | {c['days']} | {group_label(c['days'], bounds)} "
              f"| {money(c['pnl'])} | {c['ret'] * 100:.1f}% |")

    if unmatched or bad:
        print("\n### 对不上、拿不准的记录（没有猜，单独列出）\n")
        for r, why in unmatched:
            print(f"- 第 {r['line']} 行 {r['date']} {r['code']} {r['side']} {r['qty']:g}@{r['price']:g}：{why}")
        for line, why in bad:
            print(f"- 第 {line} 行：{why}")

    if open_pos:
        print("\n### 未清仓（不计入统计）\n")
        for code, name, q, start in open_pos:
            print(f"- {code} {name} · 持有 {q:g} · 自 {start}")

    if a.out:
        with open(a.out, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["code", "name", "buy_date", "sell_date", "holding_days", "group", "pnl", "return"])
            for c in sorted(closed, key=lambda c: c["sell_date"]):
                w.writerow([c["code"], c["name"], c["buy_date"], c["sell_date"], c["days"],
                            group_label(c["days"], bounds), round(c["pnl"], 2), round(c["ret"], 4)])
        print(f"\n已清仓明细已存到 {a.out}")


if __name__ == "__main__":
    main()
