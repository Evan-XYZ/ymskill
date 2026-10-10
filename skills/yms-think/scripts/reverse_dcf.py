#!/usr/bin/env python3
"""反向 DCF：从当前市值倒推市场隐含的年复合增速。只用标准库。

不问「值多少钱」，只回答：要支撑当前市值，未来 N 年自由现金流必须以多高的速度增长。

两段式模型：
    价值 = Σ(t=1..N) FCF0·(1+g)^t / (1+r)^t  +  [FCF0·(1+g)^N·(1+gT) / (r−gT)] / (1+r)^N
    求 g，使 价值 = 目标值。目标值 = 市值 + 净负债（净现金写负数）。

单位随意，前后一致即可（比如都用亿元）。

用法：
    python3 reverse_dcf.py --market-cap 5000 --fcf 120
    python3 reverse_dcf.py --market-cap 5000 --fcf 120 --rate 0.09 --terminal 0.025 --years 3,5,10
    python3 reverse_dcf.py --market-cap 5000 --fcf 120 --net-debt -300     # 有 300 净现金

口径提醒：
    · 用「股权自由现金流」时，--net-debt 保持 0；
    · 用「公司自由现金流（FCFF）」时，把净负债填进 --net-debt；
    · 基准 FCF 为负或接近 0 时，反向 DCF 不适用，脚本会直接说明。
"""

import argparse
import sys


def dcf_value(fcf0, g, r, gt, years):
    value = 0.0
    fcf = fcf0
    for t in range(1, years + 1):
        fcf *= 1 + g
        value += fcf / (1 + r) ** t
    terminal = fcf * (1 + gt) / (r - gt)
    return value + terminal / (1 + r) ** years


def implied_growth(target, fcf0, r, gt, years, lo=-0.5, hi=3.0):
    """二分法求隐含增速。价值随 g 单调递增。"""
    if dcf_value(fcf0, hi, r, gt, years) < target:
        return None  # 增速 300% 都撑不起，视为超出范围
    if dcf_value(fcf0, lo, r, gt, years) > target:
        return lo  # 负增长 50% 也高于目标值，市场定价极低
    for _ in range(200):
        mid = (lo + hi) / 2
        if dcf_value(fcf0, mid, r, gt, years) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def pct(x):
    if x is None:
        return "> 300%"
    if x <= -0.5:
        return "≤ -50%"
    return f"{x * 100:.1f}%"


def main():
    p = argparse.ArgumentParser(description="反向 DCF：倒推当前市值隐含的增长要求")
    p.add_argument("--market-cap", type=float, required=True, help="当前市值")
    p.add_argument("--fcf", type=float, required=True, help="基准自由现金流（最近一年或 TTM）")
    p.add_argument("--rate", type=float, default=0.09, help="折现率，默认 0.09")
    p.add_argument("--terminal", type=float, default=0.025, help="永续增长率，默认 0.025")
    p.add_argument("--years", default="3,5", help="显性预测期（年），逗号分隔，默认 3,5")
    p.add_argument("--net-debt", type=float, default=0.0, help="净负债，净现金写负数；默认 0")
    a = p.parse_args()

    if a.fcf <= 0:
        print("基准自由现金流 ≤ 0：反向 DCF 不适用。换成收入或利润的情景推演，或者等现金流转正再用。")
        sys.exit(0)
    if a.rate <= a.terminal:
        print("折现率必须大于永续增长率。")
        sys.exit(1)

    target = a.market_cap + a.net_debt
    years_list = [int(y) for y in a.years.split(",") if y.strip()]

    print(f"## 反向 DCF\n")
    print(f"- 目标值（市值 + 净负债）：{target:,.2f}")
    print(f"- 基准 FCF：{a.fcf:,.2f}　当前隐含倍数：{target / a.fcf:.1f} 倍")
    print(f"- 折现率 {pct(a.rate)}　永续增长 {pct(a.terminal)}\n")

    print("### 1. 隐含年复合增速\n")
    print("| 显性期 | 隐含年复合增速 | 期末 FCF 是现在的几倍 |")
    print("|:---|---:|---:|")
    base = {}
    for n in years_list:
        g = implied_growth(target, a.fcf, a.rate, a.terminal, n)
        base[n] = g
        mult = "—" if g is None else f"{(1 + g) ** n:.2f} 倍"
        print(f"| {n} 年 | {pct(g)} | {mult} |")

    print("\n### 2. 敏感性：实际增速比隐含要求低 30% / 50%，对应价值相对当前市值\n")
    print("| 显性期 | 隐含增速 | 打七折 | 价值较市值 | 打五折 | 价值较市值 |")
    print("|:---|---:|---:|---:|---:|---:|")
    skipped = False
    for n in years_list:
        g = base[n]
        if g is None or g <= 0:
            print(f"| {n} 年 | {pct(g)} | — | — | — | — |")
            skipped = True
            continue
        row = [f"{n} 年", pct(g)]
        for k in (0.7, 0.5):
            v = dcf_value(a.fcf, g * k, a.rate, a.terminal, n) - a.net_debt
            row += [pct(g * k), pct(v / a.market_cap - 1)]
        print("| " + " | ".join(row) + " |")
    if skipped:
        print("\n隐含增速 ≤ 0 或超出范围的行不做折扣：市场定价里已经没有增长要求，或者要求高到模型撑不起。")

    print("\n### 3. 折现率 × 永续增长 对隐含增速的影响（显性期取第一个）\n")
    n0 = years_list[0]
    rates = [a.rate - 0.01, a.rate, a.rate + 0.01]
    terms = [a.terminal - 0.005, a.terminal, a.terminal + 0.005]
    print("| 折现率 \\ 永续 | " + " | ".join(pct(t) for t in terms) + " |")
    print("|:---|" + "---:|" * len(terms))
    for r in rates:
        cells = []
        for t in terms:
            cells.append("—" if r <= t else pct(implied_growth(target, a.fcf, r, t, n0)))
        print(f"| {pct(r)} | " + " | ".join(cells) + " |")

    print("\n> 这是对市场预期的度量，不是估值结论，也不是目标价。")


if __name__ == "__main__":
    main()
