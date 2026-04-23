#!/usr/bin/env python3
"""
Langfuse评测数据聚合统计脚本

用法:
    python langfuse_ops.py --from "2026-04-21" --to "2026-04-22" \
        --dev "DeepSeek V3.2" --test "Qwen3.5-Plus" \
        --dev-user "sys-user-dev" --test-user "sys-user-test"

输出:
    JSON格式的统计数据，可直接用于生成评测报告
"""

import json
import os
import sys
import argparse
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import math

# Langfuse配置 - 从环境变量或直接设置
def setup_langfuse():
    """初始化Langfuse客户端"""
    if not os.environ.get("LANGFUSE_SECRET_KEY"):
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-952b3071-8b22-41fc-ab65-1dd8fd4355a6"
    if not os.environ.get("LANGFUSE_PUBLIC_KEY"):
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-20b6b4d0-0873-4255-b4bf-826891ee965c"
    if not os.environ.get("LANGFUSE_BASE_URL"):
        os.environ["LANGFUSE_BASE_URL"] = "http://172.28.40.170:3000"

    from langfuse import get_client
    return get_client()


def fetch_scores(langfuse, user_ids, from_ts, to_ts, trace_tags=None):
    """
    从Langfuse获取scores数据

    Args:
        langfuse: Langfuse客户端
        user_ids: 用户ID列表 [dev_user_id, test_user_id]
        from_ts: 开始时间
        to_ts: 结束时间
        trace_tags: trace标签过滤

    Returns:
        所有scores数据列表
    """
    if trace_tags is None:
        trace_tags = ["message"]

    all_scores = []
    limit = 100

    for user_id in user_ids:
        page = 1
        while True:
            resp = langfuse.api.scores.get_many(
                user_id=user_id,
                trace_tags=trace_tags,
                from_timestamp=from_ts,
                to_timestamp=to_ts,
                page=page,
                limit=limit,
            ).model_dump()

            for s in resp["data"]:
                s["_user_id"] = user_id
                all_scores.append(s)

            meta = resp["meta"]
            if page >= meta["total_pages"]:
                break
            page += 1

    return all_scores


def normalize_metric_name(name, user_id, dev_user, test_user):
    """
    规范化指标名称，去除-dev/-test后缀

    Args:
        name: 原始指标名称 (如 "导购引导问题相关性-dev")
        user_id: 用户ID
        dev_user: dev用户ID
        test_user: test用户ID

    Returns:
        规范化后的指标名称 (如 "导购引导问题相关性")
    """
    # 去除常见的后缀
    suffixes_to_remove = ["-dev", "-test", f"-{dev_user}", f"-{test_user}"]
    normalized = name
    for suffix in suffixes_to_remove:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
            break
    return normalized


def aggregate_stats(all_scores, dev_user, test_user):
    """
    聚合并计算统计数据

    Args:
        all_scores: 所有scores数据
        dev_user: dev用户ID (用于规范化指标名)
        test_user: test用户ID (用于规范化指标名)

    Returns:
        按user_id和指标名分组的统计数据
    """
    # grouped[user_id][score_name] = [values...]
    grouped = defaultdict(lambda: defaultdict(list))

    for s in all_scores:
        if s["data_type"] != "NUMERIC":
            continue
        if s["value"] is None:
            continue
        user_id = s["_user_id"]
        # 规范化指标名称，去除-dev/-test后缀
        normalized_name = normalize_metric_name(s["name"], user_id, dev_user, test_user)
        grouped[user_id][normalized_name].append(s["value"])

    stats = {}
    for user_id, name_map in grouped.items():
        stats[user_id] = {}
        for name, values in name_map.items():
            n = len(values)
            total = sum(values)
            mean = total / n
            variance = sum((v - mean) ** 2 for v in values) / n
            std_dev = math.sqrt(variance)
            stats[user_id][name] = {
                "total": n,
                "mean": round(mean, 4),
                "std_dev": round(std_dev, 4),
            }

    return stats


def fetch_performance_metrics(langfuse, from_ts, to_ts, user_id_prefix="sys-user-"):
    """
    从Langfuse获取性能指标（延迟、成本等）

    Args:
        langfuse: Langfuse客户端
        from_ts: 开始时间 (UTC datetime)
        to_ts: 结束时间 (UTC datetime)
        user_id_prefix: 用户ID前缀过滤

    Returns:
        按userId分组的性能指标数据（延迟单位：秒）
        {
            "sys-user-dev": {"count": 150, "p95_latency": 32.02, "p50_latency": 15.32, "avg_latency": 16.82, "total_cost": 2.006},
            "sys-user-test": {"count": 150, "p95_latency": 14.59, "p50_latency": 6.18, "avg_latency": 7.79, "total_cost": 0.784}
        }
    """
    # 构建查询 - 时间需要转换为ISO格式
    from_iso = from_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
    to_iso = to_ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    query = f"""
    {{
      "view": "traces",
      "metrics": [
        {{"measure": "count", "aggregation": "count"}},
        {{"measure": "latency", "aggregation": "p95"}},
        {{"measure": "latency", "aggregation": "p50"}},
        {{"measure": "latency", "aggregation": "avg"}},
        {{"measure": "totalCost", "aggregation": "sum"}}
      ],
      "filters": [{{
          "column": "metadata",
          "operator": "contains",
          "key": "user_id",
          "value": "{user_id_prefix}",
          "type": "stringObject"
        }}],
      "dimensions": [{{"field": "userId"}}],
      "fromTimestamp": "{from_iso}",
      "toTimestamp": "{to_iso}"
    }}
    """

    try:
        resp = langfuse.api.legacy.metrics_v1.metrics(query=query).model_dump()
        performance_data = {}

        for item in resp.get("data", []):
            user_id = item.get("userId")
            # 原始延迟数据单位为毫秒，转换为秒
            performance_data[user_id] = {
                "count": item.get("count_count", 0),
                "p95_latency": round(item.get("p95_latency", 0) / 1000, 2),  # 秒
                "p50_latency": round(item.get("p50_latency", 0) / 1000, 2),  # 秒
                "avg_latency": round(item.get("avg_latency", 0) / 1000, 2),  # 秒
                "total_cost": round(item.get("sum_totalCost", 0), 6),  # 美元
            }

        return performance_data
    except Exception as e:
        print(f"警告: 获取性能指标失败: {e}", file=sys.stderr)
        return {}


def generate_report_data(stats, config, performance_data=None):
    """
    生成报告所需的JSON数据结构

    Args:
        stats: 聚合统计数据
        config: 配置信息 (dev_name, test_name, dev_user, test_user)
        performance_data: 性能指标数据 (可选)

    Returns:
        报告数据结构
    """
    dev_user = config["dev_user"]
    test_user = config["test_user"]
    dev_name = config["dev_name"]
    test_name = config["test_name"]

    # 获取所有指标名称（取两个用户的并集）
    all_metrics = set()
    if dev_user in stats:
        all_metrics.update(stats[dev_user].keys())
    if test_user in stats:
        all_metrics.update(stats[test_user].keys())

    # 构建metrics列表
    metrics = []
    for metric_name in sorted(all_metrics):
        metric_data = {"name": metric_name, "data": {}}

        # Dev数据
        if dev_user in stats and metric_name in stats[dev_user]:
            metric_data["data"]["dev"] = stats[dev_user][metric_name]
        else:
            metric_data["data"]["dev"] = {"total": 0, "mean": 0, "std_dev": 0}

        # Test数据
        if test_user in stats and metric_name in stats[test_user]:
            metric_data["data"]["test"] = stats[test_user][metric_name]
        else:
            metric_data["data"]["test"] = {"total": 0, "mean": 0, "std_dev": 0}

        metrics.append(metric_data)

    # 构建完整报告数据
    report_data = {
        "title": f"{dev_name} vs {test_name} 模型评测报告",
        "subtitle": f"评测时间段: {config['from_date']} 至 {config['to_date']}",
        "models": [
            {"id": "dev", "name": dev_name, "user_id": dev_user},
            {"id": "test", "name": test_name, "user_id": test_user}
        ],
        "metrics": metrics,
        "config": {
            "from_date": config["from_date"],
            "to_date": config["to_date"],
            "trace_tags": config.get("trace_tags", ["message"])
        }
    }

    # 添加性能指标
    if performance_data:
        performance = {"dev": None, "test": None}

        if dev_user in performance_data:
            performance["dev"] = performance_data[dev_user]

        if test_user in performance_data:
            performance["test"] = performance_data[test_user]

        report_data["performance"] = performance

    return report_data


def parse_datetime(dt_str):
    """
    解析时间字符串，支持两种格式:
    - YYYY-MM-DD
    - YYYY-MM-DD HH:MM:SS

    输入时间被视为本地时间（北京时间 UTC+8），然后转换为 UTC
    """
    from datetime import timedelta

    dt_str = dt_str.strip()
    try:
        # 尝试解析带时分秒的格式
        local_dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # 尝试解析只有日期的格式
        local_dt = datetime.strptime(dt_str, "%Y-%m-%d")

    # 本地时间转换为 UTC（北京时间 UTC+8）
    utc_offset = timedelta(hours=8)
    utc_dt = local_dt - utc_offset
    return utc_dt.replace(tzinfo=timezone.utc)


def main():
    parser = argparse.ArgumentParser(description="Langfuse评测数据聚合统计")
    parser.add_argument("--from", dest="from_date", required=True, help="开始时间 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--to", dest="to_date", required=True, help="结束时间 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--dev", dest="dev_name", required=True, help="Dev模型名称")
    parser.add_argument("--test", dest="test_name", required=True, help="Test模型名称")
    parser.add_argument("--dev-user", dest="dev_user", default="sys-user-dev", help="Dev用户ID")
    parser.add_argument("--test-user", dest="test_user", default="sys-user-test", help="Test用户ID")
    parser.add_argument("--trace-tags", dest="trace_tags", nargs="+", default=["message"], help="Trace标签过滤")
    parser.add_argument("--output", "-o", dest="output", help="输出文件路径 (默认stdout)")

    args = parser.parse_args()

    # 解析时间（支持时分秒）
    from_ts = parse_datetime(args.from_date)
    to_ts = parse_datetime(args.to_date)

    # 初始化Langfuse
    print(f"正在连接Langfuse...", file=sys.stderr)
    langfuse = setup_langfuse()

    if not langfuse.auth_check():
        print("错误: Langfuse认证失败", file=sys.stderr)
        sys.exit(1)

    print(f"Langfuse连接成功!", file=sys.stderr)

    # 获取数据
    user_ids = [args.dev_user, args.test_user]
    print(f"正在获取 {args.from_date} 至 {args.to_date} 的评测数据...", file=sys.stderr)

    all_scores = fetch_scores(langfuse, user_ids, from_ts, to_ts, args.trace_tags)
    print(f"获取到 {len(all_scores)} 条score记录", file=sys.stderr)

    # 获取性能指标
    print(f"正在获取性能指标...", file=sys.stderr)
    performance_data = fetch_performance_metrics(langfuse, from_ts, to_ts)
    if performance_data:
        print(f"获取到 {len(performance_data)} 个用户的性能数据", file=sys.stderr)

    # 聚合统计
    stats = aggregate_stats(all_scores, args.dev_user, args.test_user)

    # 生成报告数据
    config = {
        "dev_name": args.dev_name,
        "test_name": args.test_name,
        "dev_user": args.dev_user,
        "test_user": args.test_user,
        "from_date": args.from_date,
        "to_date": args.to_date,
        "trace_tags": args.trace_tags
    }

    report_data = generate_report_data(stats, config, performance_data)

    # 输出
    output_json = json.dumps(report_data, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"报告数据已保存至: {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # 打印摘要
    print(f"\n=== 数据摘要 ===", file=sys.stderr)
    print(f"Dev模型 ({args.dev_name}):", file=sys.stderr)
    if args.dev_user in stats:
        for name, data in stats[args.dev_user].items():
            print(f"  - {name}: mean={data['mean']:.4f}, std={data['std_dev']:.4f}, n={data['total']}", file=sys.stderr)

    print(f"Test模型 ({args.test_name}):", file=sys.stderr)
    if args.test_user in stats:
        for name, data in stats[args.test_user].items():
            print(f"  - {name}: mean={data['mean']:.4f}, std={data['std_dev']:.4f}, n={data['total']}", file=sys.stderr)

    # 打印性能摘要
    if performance_data:
        print(f"\n=== 性能指标 ===", file=sys.stderr)
        if args.dev_user in performance_data:
            p = performance_data[args.dev_user]
            print(f"Dev模型 ({args.dev_name}):", file=sys.stderr)
            print(f"  - 请求数: {p['count']}", file=sys.stderr)
            print(f"  - 平均延迟: {p['avg_latency']:.2f}s (P50: {p['p50_latency']:.2f}s, P95: {p['p95_latency']:.2f}s)", file=sys.stderr)
            print(f"  - 总成本: ${p['total_cost']:.6f}", file=sys.stderr)

        if args.test_user in performance_data:
            p = performance_data[args.test_user]
            print(f"Test模型 ({args.test_name}):", file=sys.stderr)
            print(f"  - 请求数: {p['count']}", file=sys.stderr)
            print(f"  - 平均延迟: {p['avg_latency']:.2f}s (P50: {p['p50_latency']:.2f}s, P95: {p['p95_latency']:.2f}s)", file=sys.stderr)
            print(f"  - 总成本: ${p['total_cost']:.6f}", file=sys.stderr)


if __name__ == "__main__":
    main()
