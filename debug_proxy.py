import time
import os
from desktop_env.desktop_env import DesktopEnv

# === 1. 配置你的环境路径 (请根据实际情况修改) ===
# 确保指向你的 qcow2 文件
path_to_vm = "/home/zhangxiuhui/projects/OSWorld/docker_vm_data/Ubuntu.qcow2"

# === 2. 模拟配置参数 ===
# 这里我们手动构造一个配置，模拟 run.py 的行为
env_config = {
    "path_to_vm": path_to_vm,
    "require_terminal": True,
    "headless": True,      # 必须是 True，因为我们在服务器上跑
    "action_space": "pyautogui",
    "screen_size": (1920, 1080),
    "snapshot_name": "snapshot_name" # 只要能启动就行，名字暂时不重要
}

# === 3. 【核心】注入代理配置 ===
# 这是验证刚才修改的代码是否生效的关键
# 我们直接在当前进程的环境变量里设好，DesktopEnv 初始化时会传给 Docker
proxy_url = "http://172.17.0.1:7899"
os.environ["http_proxy"] = proxy_url
os.environ["https_proxy"] = proxy_url
# 注意：如果你之前修改了 desktop_env.py 的源码来注入 environment，这里其实是双重保险

print(f"🚀 Starting OSWorld Debug Environment with Proxy: {proxy_url}")

# === 4. 启动环境 ===
env = DesktopEnv(
    provider_name="docker",
    path_to_vm=path_to_vm,
    action_space="pyautogui",
    screen_size=(1920, 1080),
    headless=True,
    os_type="Ubuntu",
    enable_proxy=False,
)

# 重置环境，等待系统完全启动
obs = env.reset(task_config={"id": "0", "instruction": "Test network"})

print("\n✅ Environment Started!")
print("==================================================")
print("现在虚拟机正在运行中。")
print("请配置 SSH 隧道连接 VNC 端口 (默认 5900 或 8006) 查看桌面。")
print("脚本将挂起 10 分钟供你调试...")
print("==================================================")

# === 5. 挂起脚本，不要退出 ===
try:
    # 保持 Docker 运行，让你有机会连进去
    time.sleep(600) 
except KeyboardInterrupt:
    print("Stopping...")
finally:
    env.close()