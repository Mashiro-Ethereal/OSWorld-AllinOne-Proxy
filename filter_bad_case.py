import shutil
import json
from pathlib import Path
from collections import defaultdict

def process_and_analyze_osworld(source_root_str):
    source_root = Path(source_root_str)
    
    # ================= 1. 路径定义 =================
    # 基础目录 (result-xxxxxx 层级)
    base_output_dir = source_root.parents[2]
    
    # 目标路径
    target_bad_root = base_output_dir / "bad-case"
    target_variant_root = base_output_dir / "variant-case"
    analysis_json_path = base_output_dir / "analysis.json"
    
    print(f"🚀 开始处理任务...")
    print(f"📂 源目录: {source_root}")
    print(f"📄 统计结果将保存至: {analysis_json_path}")

    if not source_root.exists():
        print(f"❌ 错误: 源目录不存在 -> {source_root}")
        return

    # ================= 2. 数据容器初始化 =================
    # 存储原始数据用于计算
    raw_data = defaultdict(list)
    
    # 计数器
    stats = {
        "filtered_cases": {
            "bad_case_copied": 0,    # 0分案例
            "variant_case_copied": 0 # 含caption案例
        },
        "process_status": {
            "valid_tasks": 0,        # 成功解析数据的任务
            "missing_token_file": 0  # 缺少 token_usage 的任务
        }
    }

    # ================= 3. 单次遍历核心循环 =================
    for task_type_dir in sorted(source_root.iterdir()):
        if not task_type_dir.is_dir():
            continue
            
        task_type_name = task_type_dir.name

        for task_id_dir in task_type_dir.iterdir():
            if not task_id_dir.is_dir():
                continue
            
            task_id_name = task_id_dir.name
            
            # --- 文件路径预定义 ---
            token_file = task_id_dir / "token_usage.json"
            traj_file = task_id_dir / "traj.jsonl"
            result_file = task_id_dir / "result.txt"
            caption_file = task_id_dir / "fact_captions.jsonl"

            # --- A. 获取分数与状态 (用于筛选) ---
            current_score = 0.0
            score_content = ""
            if result_file.exists():
                try:
                    score_content = result_file.read_text(encoding='utf-8').strip()
                    if score_content:
                        current_score = float(score_content)
                except ValueError:
                    pass

            has_caption = caption_file.exists()
            is_score_zero = (score_content != "" and current_score == 0.0)

            # --- B. 执行复制逻辑 (Bad Case / Variant Case) ---
            # 1. 0分 -> bad-case
            if is_score_zero:
                dest = target_bad_root / task_type_name / task_id_name
                try:
                    shutil.copytree(task_id_dir, dest, dirs_exist_ok=True)
                    stats["filtered_cases"]["bad_case_copied"] += 1
                except Exception as e:
                    print(f"⚠️ 复制失败 (Bad): {task_id_name} - {e}")

            # 2. Caption -> variant-case
            if has_caption:
                dest = target_variant_root / task_type_name / task_id_name
                try:
                    shutil.copytree(task_id_dir, dest, dirs_exist_ok=True)
                    stats["filtered_cases"]["variant_case_copied"] += 1
                except Exception as e:
                    print(f"⚠️ 复制失败 (Variant): {task_id_name} - {e}")

            # --- C. 执行数据收集逻辑 (Analysis) ---
            if not token_file.exists():
                stats["process_status"]["missing_token_file"] += 1
                continue 

            try:
                # 读取 Token
                token_data = json.loads(token_file.read_text(encoding='utf-8'))
                p_tokens = token_data.get("prompt_tokens", 0)
                c_tokens = token_data.get("completion_tokens", 0)
                cached_t = token_data.get("cached_tokens", 0)
                
                if "cache_hit_rate" in token_data:
                    h_rate = token_data["cache_hit_rate"]
                else:
                    h_rate = (cached_t / p_tokens) if p_tokens > 0 else 0.0

                # 读取 Steps
                steps_count = 0
                if traj_file.exists():
                    with open(traj_file, 'rb') as f:
                        steps_count = sum(1 for _ in f)

                # 存入原始数据
                raw_data[task_type_name].append({
                    "task_id": task_id_name, # 可选：如果需要记录具体哪个ID得分多少
                    "steps": steps_count,
                    "prompt": p_tokens,
                    "completion": c_tokens,
                    "cached": cached_t,
                    "hit_rate": h_rate,
                    "score": current_score 
                })
                stats["process_status"]["valid_tasks"] += 1

            except Exception as e:
                print(f"⚠️ 解析数据错误 {task_id_name}: {e}")

    # ================= 4. 计算统计并保存 JSON =================
    final_report = calculate_statistics(raw_data, stats)
    
    try:
        with open(analysis_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=4, ensure_ascii=False)
        print(f"✅ 处理完成。")
        print(f"   - Bad Cases (0分): {stats['filtered_cases']['bad_case_copied']}")
        print(f"   - Variant Cases (Caption): {stats['filtered_cases']['variant_case_copied']}")
        print(f"   - JSON已保存: {analysis_json_path}")
    except Exception as e:
        print(f"❌ 保存JSON失败: {e}")

def calculate_statistics(raw_data, base_stats):
    """
    将原始列表数据转换为聚合统计数据 (Sum, Avg)
    """
    detailed_stats = {}
    all_metrics = defaultdict(list)
    
    # 1. 计算分任务类型的统计
    for task_type, records in raw_data.items():
        count = len(records)
        if count == 0: continue
        
        sum_score = sum(r['score'] for r in records)
        
        # 计算该类型的各项平均值
        keys_to_avg = ['steps', 'prompt', 'completion', 'cached', 'hit_rate']
        averages = {k: sum(r[k] for r in records) / count for k in keys_to_avg}
        
        detailed_stats[task_type] = {
            "count": count,
            "total_score": sum_score,
            "success_rate": sum_score / count, # 平均分即成功率
            "averages": averages
        }

        # 收集用于全局计算
        for r in records:
            for k, v in r.items():
                if isinstance(v, (int, float)):
                    all_metrics[k].append(v)

    # 2. 计算全局统计 (Global)
    global_stats = {}
    total_n = len(all_metrics['prompt'])
    
    if total_n > 0:
        total_score = sum(all_metrics['score'])
        
        keys_to_avg = ['steps', 'prompt', 'completion', 'cached', 'hit_rate']
        global_avgs = {k: sum(all_metrics[k]) / total_n for k in keys_to_avg}
        
        global_stats = {
            "total_count": total_n,
            "total_score": total_score,
            "global_success_rate": total_score / total_n,
            "averages": global_avgs
        }

    # 3. 组装最终字典
    return {
        "meta": {
            "process_stats": base_stats["process_status"],
            "filter_stats": base_stats["filtered_cases"]
        },
        "global_summary": global_stats,
        "details_by_type": detailed_stats
    }

if __name__ == "__main__":
    src_paths = [
        "/home/zhangxiuhui/projects/OSWorld/results-01201005/pyautogui/screenshot/gpt-5",
    ]
    for src_path in src_paths:
        process_and_analyze_osworld(src_path)