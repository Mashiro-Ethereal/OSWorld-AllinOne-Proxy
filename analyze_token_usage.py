import json
from pathlib import Path

def analyze_token_details(source_root_str):
    source_root = Path(source_root_str)
    # 初始化各项指标
    metrics = {
        "prompt": 0,
        "completion": 0,
        "cached": 0,
        "tasks": 0
    }

    if not source_root.exists():
        return None

    # 遍历：Task Type -> Task ID
    for task_type_dir in source_root.iterdir():
        if not task_type_dir.is_dir(): continue
        
        for task_id_dir in task_type_dir.iterdir():
            if not task_id_dir.is_dir(): continue
            
            token_file = task_id_dir / "token_usage.json"
            if token_file.exists():
                try:
                    data = json.loads(token_file.read_text(encoding='utf-8'))
                    # 累加各项具体数值
                    metrics["prompt"] += data.get("prompt_tokens", 0)
                    metrics["completion"] += data.get("completion_tokens", 0)
                    metrics["cached"] += data.get("cached_tokens", 0)
                    metrics["tasks"] += 1
                except Exception:
                    pass

    return metrics

if __name__ == "__main__":
    src_paths = [
        "/home/zhangxiuhui/projects/OSWorld/results-01201005/pyautogui/screenshot/gpt-5"
    ]

    # 总计计数器
    g_prompt, g_completion, g_cached, g_tasks = 0, 0, 0, 0

    # 打印表头
    header = f"{'Batch Directory':<20} | {'Tasks':<5} | {'Input':<12} | {'Cache':<12} | {'Output':<12}"
    print(header)
    print("-" * len(header))

    for path in src_paths:
        m = analyze_token_details(path)
        if m:
            p_name = Path(path).parents[2].name # 提取 result-xxxx 目录名
            print(f"{p_name:<20} | {m['tasks']:<5} | {m['prompt']:>12,} | {m['cached']:>12,} | {m['completion']:>12,}")
            
            # 累加全局数据
            g_prompt += m['prompt']
            g_completion += m['completion']
            g_cached += m['cached']
            g_tasks += m['tasks']

    print("-" * len(header))
    print(f"{'GRAND TOTAL':<20} | {g_tasks:<5} | {g_prompt:>12,} | {g_cached:>12,} | {g_completion:>12,}")
    
    total_tokens = g_prompt + g_completion
    print(f"\n📢 总计消耗 (Input + Output): {total_tokens:,} Tokens")