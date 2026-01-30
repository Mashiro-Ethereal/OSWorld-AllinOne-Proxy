import datetime
import json
import logging
import os
import time
from typing import *
from wrapt_timeout_decorator import *

logger = logging.getLogger("desktopenv.experiment")


def run_single_example(
    agent, env, example, max_steps, instruction, args, example_result_dir, scores
):
    runtime_logger = setup_logger(example, example_result_dir)

    try:
        agent.reset(runtime_logger)
    except Exception as e:
        agent.reset()
    
    # modify
    try:
        # 尝试获取 engine 实例
        llm_generator_engine = agent.executor.generator_agent.engine
        llm_reflection_engine = agent.executor.reflection_agent.engine
        # 在任务开始前，强制清零计数器
        if hasattr(llm_generator_engine, "reset_usage"):
            llm_generator_engine.reset_usage()
            runtime_logger.info("Generator token reset.")
        if hasattr(llm_reflection_engine, "reset_usage"):
            llm_reflection_engine.reset_usage()
            runtime_logger.info("Reflection token reset.")
    except AttributeError:
        llm_generator_engine = None
        llm_reflection_engine = None
        runtime_logger.warning("Could not find LLM Engine to reset usage stats.")
    # modify end

    env.reset(task_config=example)
    time.sleep(60)  # Wait for the environment to be ready
    obs = env._get_obs()  # Get the initial observation

    with open(os.path.join(example_result_dir, f"step_0.png"), "wb") as _f:
        _f.write(obs["screenshot"])

    with open(
        os.path.join(example_result_dir, "instruction.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(instruction)

    done = False
    step_idx = 0
    # env.controller.start_recording()
    while not done and step_idx < max_steps:
        response, actions = agent.predict(instruction, obs)
        for action in actions:
            action_timestamp = datetime.datetime.now().strftime("%Y%m%d@%H%M%S")
            logger.info("Step %d: %s", step_idx + 1, action)
            obs, reward, done, info = env.step(action, args.sleep_after_execution)

            logger.info("Reward: %.2f", reward)
            logger.info("Done: %s", done)
            # Save screenshot and trajectory information
            with open(
                os.path.join(
                    example_result_dir, f"step_{step_idx + 1}_{action_timestamp}.png"
                ),
                "wb",
            ) as _f:
                _f.write(obs["screenshot"])

            response.update(
                {
                    "step_num": step_idx + 1,
                    "action_timestamp": action_timestamp,
                    "action": action,
                    "reward": reward,
                    "done": done,
                    "info": info,
                    "screenshot_file": f"step_{step_idx + 1}_{action_timestamp}.png",
                }
            )
            with open(
                os.path.join(example_result_dir, "traj.jsonl"), "a", encoding="utf-8"
            ) as f:
                f.write(json.dumps(response, ensure_ascii=False))
                f.write("\n")
            if done:
                logger.info("The episode is done.")
                break
        step_idx += 1
    result = env.evaluate()
    logger.info("Result: %.2f", result)
    scores.append(result)

    # modify
    if llm_generator_engine and llm_reflection_engine:
        generator_data = llm_generator_engine.get_usage_report()
        reflection_usage = llm_reflection_engine.get_usage_report()
        
        usage_data = {
            "prompt_tokens": generator_data["prompt_tokens"] + reflection_usage["prompt_tokens"],
            "completion_tokens": generator_data["completion_tokens"] + reflection_usage["completion_tokens"],
            "cached_tokens": generator_data["cached_tokens"] + reflection_usage["cached_tokens"],
            "total_tokens": generator_data["total_tokens"] + reflection_usage["total_tokens"],
        }
        
        # 必须基于总数重新计算命中率 (加权平均)，不可直接相加
        usage_data["cache_hit_rate"] = (
            usage_data["cached_tokens"] / usage_data["prompt_tokens"] 
            if usage_data["prompt_tokens"] > 0 else 0.0
        )
    
        # 打印到控制台/日志
        runtime_logger.info(f"Task Token Usage: {json.dumps(usage_data)}")
        
        # 保存到单独的 json 文件，方便后续画图分析
        usage_file = os.path.join(example_result_dir, "token_usage.json")
        with open(usage_file, "w", encoding="utf-8") as f:
            json.dump(usage_data, f, indent=4)
     # modify end

    with open(
        os.path.join(example_result_dir, "result.txt"), "w", encoding="utf-8"
    ) as f:
        f.write(f"{result}\n")
    # env.controller.end_recording(os.path.join(example_result_dir, "recording.mp4"))


def setup_logger(example, example_result_dir):
    runtime_logger = logging.getLogger(f"desktopenv.example.{example['id']}")
    runtime_logger.setLevel(logging.DEBUG)
    runtime_logger.addHandler(
        logging.FileHandler(os.path.join(example_result_dir, "runtime.log"))
    )
    return runtime_logger
