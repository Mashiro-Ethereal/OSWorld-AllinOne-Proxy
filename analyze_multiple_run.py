import json
import os
from pathlib import Path
from collections import defaultdict

# ================= 配置区域 =================
BASE_DIR = Path("/home/zhangxiuhui/projects/OSWorld/results-group-0116")

# 参与对比的 5 个文件夹名称
RUN_DIRS = [
    "results-1",
    "results-2",
    "results-3",
    "results-4",
    "results-5"
]

# 结果文件相对于 result-xxxxxx 的子路径
# 根据你之前的上下文，路径通常是 results-xxx/pyautogui/screenshot/gpt-5
SUB_PATH = Path("pyautogui/screenshot/gpt-5")

OUTPUT_FILE = BASE_DIR / "bon_error_distribution.json"
# ===========================================

def get_task_score(result_path):
    """读取 result.txt，返回浮点数分数。文件不存在或无法读取返回 0.0"""
    if result_path.exists():
        try:
            content = result_path.read_text(encoding='utf-8').strip()
            if content:
                return float(content)
        except ValueError:
            pass
    return 0.0

def analyze_runs():
    print(f"🚀 开始分析 5 个 Run 的分布情况...")
    print(f"📂 根目录: {BASE_DIR}")
    
    # 数据结构: { "task_type/task_id": { "run_name": score, ... } }
    all_tasks_data = defaultdict(dict)
    
    # 1. 遍历每个 Run 文件夹收集数据
    for run_name in RUN_DIRS:
        full_run_path = BASE_DIR / run_name / SUB_PATH
        print(f"   -> 扫描: {run_name}")
        
        if not full_run_path.exists():
            print(f"      ⚠️ 警告: 路径不存在 {full_run_path}")
            continue

        # 遍历任务类型
        for task_type_dir in full_run_path.iterdir():
            if not task_type_dir.is_dir(): continue
            
            # 遍历任务ID
            for task_id_dir in task_type_dir.iterdir():
                if not task_id_dir.is_dir(): continue
                
                # 构建唯一标识 key
                task_key = f"{task_type_dir.name}/{task_id_dir.name}"
                
                # 获取分数
                result_file = task_id_dir / "result.txt"
                score = get_task_score(result_file)
                
                # 记录该 Run 的得分
                all_tasks_data[task_key][run_name] = score

    # 2. 分析分布 (Pivot Data)
    print(f"🔄 正在聚合数据...")
    
    analysis_output = {
        "summary": {
            "total_unique_tasks": len(all_tasks_data),
            "perfect_tasks": 0,      # 5次全对
            "hard_fail_tasks": 0,    # 5次全错 (重点)
            "inconsistent_tasks": 0, # 有对有错 (BoN 潜力股)
        },
        # 详细列表
        "details": [] 
    }

    for task_key, runs_score_map in all_tasks_data.items():
        # 统计该任务在 5 个 Run 中的表现
        succeeded_runs = []
        failed_runs = []
        
        # 确保检查列表中的每一个 run，即使该 run 中没有生成该任务文件夹（视为0分）
        for run_name in RUN_DIRS:
            score = runs_score_map.get(run_name, 0.0) # 默认为 0
            if score >= 0.5: # 假设 1.0 为满分/成功
                succeeded_runs.append(run_name)
            else:
                failed_runs.append(run_name)
        
        success_count = len(succeeded_runs)
        fail_count = len(failed_runs)
        total_runs = len(RUN_DIRS)

        # 分类逻辑
        category = "unknown"
        if success_count == total_runs:
            category = "perfect"
            analysis_output["summary"]["perfect_tasks"] += 1
        elif success_count == 0:
            category = "hard_fail"
            analysis_output["summary"]["hard_fail_tasks"] += 1
        else:
            category = "inconsistent"
            analysis_output["summary"]["inconsistent_tasks"] += 1

        # 只要有过失败（fail_count > 0），就记录下来 (符合你只筛选错题的需求)
        # 如果你想看全量数据，去掉这个 if 即可
        if fail_count > 0:
            analysis_output["details"].append({
                "task_id": task_key,
                "category": category,
                "stats": {
                    "success_cnt": success_count,
                    "fail_cnt": fail_count
                },
                "distribution": {
                    "succeeded_in": succeeded_runs, # 哪几个做对了
                    "failed_in": failed_runs        # 哪几个做错了
                }
            })

    # 3. 排序：优先显示 Inconsistent (有挽救价值的)，其次是 Hard Fail
    # 为了方便查看，我们把 inconsistent 排在前面
    analysis_output["details"].sort(key=lambda x: (x['category'] != 'inconsistent', x['category']))

    # 4. 保存结果
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(analysis_output, f, indent=4, ensure_ascii=False)
        print(f"✅ 分析完成！结果已保存至: {OUTPUT_FILE}")
        print(f"📊 概览: 全错: {analysis_output['summary']['hard_fail_tasks']} | 不稳定: {analysis_output['summary']['inconsistent_tasks']} | 全对: {analysis_output['summary']['perfect_tasks']}")
    except Exception as e:
        print(f"❌ 保存文件失败: {e}")

if __name__ == "__main__":
    analyze_runs()