#!/bin/bash

# ================= 配置区域 =================
# 指定使用 3 号显卡 (对应你的第4张 A800)
export CUDA_VISIBLE_DEVICES=2

export HF_HUB_OFFLINE=1

# 设置模型路径 (HuggingFace Hub ID 或 本地绝对路径)
MODEL_PATH="ByteDance-Seed/UI-TARS-1.5-7B"

# 设置服务别名 (Agent S3 调用时用这个名字)
SERVED_NAME="ByteDance-Seed/UI-TARS-1.5-7B"

# 服务端口
PORT=8000

# 填写你的 Hugging Face Token (用于首次下载模型权重)
# 下载完成后，以后启动其实可以不需要这行，但保留着无妨

# ================= 启动命令 =================
echo "正在 GPU ${CUDA_VISIBLE_DEVICES} 上启动 vLLM 服务..."
echo "模型: ${MODEL_PATH}"
echo "端口: ${PORT}"

# 运行 vLLM OpenAI 兼容服务
# --dtype auto: 自动根据 A800 选择 bf16，性能最好
# --trust-remote-code: 必须开启，因为 UI-TARS 有自定义代码
# python -m vllm.entrypoints.openai.api_server \
#     --model $MODEL_PATH \
#     --served-model-name $SERVED_NAME \
#     --trust-remote-code \
#     --dtype auto \
#     --port $PORT
vllm serve "ByteDance-Seed/UI-TARS-1.5-7B" --gpu-memory-utilization 0.4 --max-model-len 32768
# vllm serve "ByteDance-Seed/UI-TARS-1.5-7B"