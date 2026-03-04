# hippo
python -m hippo-agent.run_muscle_mem_agent \
  --provider_name "docker" \
  --headless \
  --num_envs 1 \
  --max_steps 100 \
  --domain "all" \
  --test_all_meta_path evaluation_examples/test_nogdrive.json \
  --result_dir "results-hippo" \
  --model_provider "anthropic" \


Produce HIPPO Agent technical report
HIPPO-Agent




打开


提交




非常好。现在我梳理一下pipeline：
1 接收到任务的prompt
2 可行性检查阶段：调用各种工具，检查任务是否具有可行性。输出有三个状态。最终结束状态为FEASIBLE或者INFEASIBLE（中间可以调用ACTION）。如果INFEASIBLE则停止，如果FEASIBLE就进入worker
3 worker：首先一定写一个TODOWrite，写的不好会要求重写。还有一个scratchpad可以用于存储记忆。此外是常用的ui和code；如果认为结束了则输出done动作。
之后，就没有别的调用LLM的任务流程了。我总结的对吗？如果不对请详细告诉我


已处理 1m 21s
你的总结大方向是对的，但有 6 个关键点需要修正：

可行性阶段不只有你说的 3 种状态
InfeasibleAgent 会返回 ACTION / FEASIBLE / INFEASIBLE / NO_DECISION（还有无任务时的 no task 分支）。见 infeasible_agent.py (line 354)、infeasible_agent.py (line 559)、infeasible_agent.py (line 467)。
在总流程里，FEASIBLE、NO_DECISION、NO_TASK 都会进入执行阶段，不是只有 FEASIBLE 才进 worker。见 agent.py (line 147)。
Worker“首步一定 TodoWrite”不是硬约束
代码是“如果模型给了 TodoWrite 且条目少于 4，则触发重采样+重选”；并没有“非 TodoWrite 就强制打回”的逻辑。见 worker.py (line 479)。
Worker 结束动作不只有 done
终止分支是 done / fail / report_infeasible。见 worker.py (line 607)。
另外 done 有 guardrail：若此前没有关键执行动作（如 click/click_image/hotkey/call_code_agent），会被拒绝并重试（默认最多 3 次）。见 worker.py (line 519)、worker.py (line 347)。
“worker 之后没有别的 LLM 流程”不准确
Worker 可调用 call_code_agent，进入 Code Agent 的独立 LLM 工具循环。见 worker.py (line 579)、motor_code_agent.py (line 485)、motor_code_agent.py (line 226)。
Worker 内部单轮也可能多次调用 LLM（例如 Todo 候选重采样与选择）。见 worker.py (line 248)、worker.py (line 305)。
UI 动作后还有 grounding LLM 调用
click/click_image/drag/scroll/type(带定位) 会触发坐标 grounding 的额外模型调用。见 grounding.py (line 213)、grounding.py (line 231)。
当前默认分支里，verification/subagent 入口并未真正启用
这两条你没写出来，但确实是“目前不在主 pipeline 里”的原因之一。
你可以把 pipeline 改成这版更准确：

收到任务。
进入 infeasible phase，循环执行直到出现 INFEASIBLE（直接停）或转入 execute（FEASIBLE/NO_DECISION/NO_TASK）。
进入 worker phase，按工具循环推进；TodoWrite 是强建议但非硬强制。
worker 可直接做 UI，也可下钻 call_code_agent 进入子循环。
worker 终止条件是 done/fail/report_infeasible。
每步 UI 定位类动作可能再触发 grounding 模型调用。

repo里自称的core contribution如下，解释一下分别对应哪些内容：
Memory System (Core)
1) Working Memory (task-level)
Across multi-step tasks, HIPPO Agent stores and retrieves essential information:

Typical content: credentials/config choices, observed UI state, critical paths, completed subgoals, extracted values, TODO checkpoints, risk notes
Benefits: fewer repeated OCR/searches, less “why did we click that?” forgetting, reduced token pressure and attention dilution
Practical note: tool naming matters. Avoid semantic collisions with in-app concepts (e.g., “Notes”) to reduce model confusion.

2) Selective Retrieval
To avoid drowning the planner in noise, retrieval should be selective and structured:

inject only the minimal relevant memory per step rather than replaying long histories
store/retrieve by categories such as “facts / state / todos / risks” to reduce misreads
3) Memory-driven Context Engineering
keep only necessary recent observations (e.g., a small number of recent screenshots/states)
persist long-range information in memory; during planning/verification/convergence, prefer memory reads over scanning long histories


已处理 1m 43s
你这三条确实对应到仓库里的“Memory System (Core)”宣称，但代码里是“部分落地 + 部分愿景”。

宣称来源在 README.md (line 38)。

Working Memory (task-level) 对应内容
主要载体是 scratchpad、todo_board、execution_history、pending_feasible_report 这些任务级状态，初始化在 grounding.py (line 81) 和 grounding.py (line 158)。
写入/读取工具是 TodoWrite 与 save/read_scratchpad，定义在 todo.py (line 54)、scratchpad.py (line 51)。
执行轨迹也会记录（worker/infeasible 都会写入），见 worker.py (line 359)、infeasible_agent.py (line 297)。
评价：这部分是“有实体实现”的。
Selective Retrieval 对应内容
有一定“按需读”的能力：read_scratchpad(limit) 支持只取最近 N 条，见 scratchpad.py (line 63)。
有历史截断接口：get_execution_history_text(max_entries)，见 grounding.py (line 381)。
但 README 提的 “facts/state/todos/risks 分类存取” 在代码里没有专门数据结构或检索器（更像设计目标）。
评价：部分实现，结构化检索还不完整。
Memory-driven Context Engineering 对应内容
已实现的一点：上下文里只保留最近图片，避免视觉上下文膨胀，见 worker.py (line 386)。
任务切换会清理状态（history/scratchpad/feasible_report），见 grounding.py (line 368)。
但“把长程记忆稳定注入规划上下文”当前分支有两处被关掉：
worker 里 feasible_report_message 关闭，worker.py (line 414)
feasible report 的 pop 直接返回 None，grounding.py (line 353)
scratchpad 自动注入也被注释，worker.py (line 430)
评价：框架有，但“记忆驱动上下文注入”在当前代码里是弱化/部分关闭状态。
一句话总结：
这三条在 repo 中不是“纯口号”，但实现成熟度不同。Working Memory 最实；Selective Retrieval 与 Memory-driven Context Engineering 目前更接近“半落地 + 可继续补全”。


这个repo是基于Agent S系统的。但是与Agent S3系统采用Best of N的形式不同，hippo的设计目标是尽可能提高单次的成功率，并且现在也达到了sota。总结一下，相比于原始的agent

这个repo是基于Agent S系统的。但是与Agent S3系统采用Best of N的形式不同，hippo的设计目标是尽可能提高单次的成功率，并且现在也达到了sota。总结一下，通过哪些方面的改进，他让单次做的更好了


已处理 2m 9s
你这个判断很准：HIPPO 的核心不是“多跑几条轨迹再挑最好（BoN）”，而是把预算放在单条轨迹内的控制点，提高一次跑成的概率。

主要改进点可以总结为：

前置可行性筛查，避免在不可能任务上消耗并跑偏
先进入 infeasible phase，判定 FEASIBLE/INFEASIBLE（中间可 ACTION），不可行直接终止。
这能显著减少“错误累积”。
代码：agent.py (line 129), infeasible_agent.py (line 559)
对计划质量做门控（不是放任模型随手给 plan）
首次 TodoWrite 如果条目太少（<4），会强制多次重采样候选，再择优。
本质是“单次内局部 N 选 1”，而不是全流程 BoN。
代码：worker.py (line 479)
对结束动作做门控，抑制“过早 done”
若还没有关键执行证据（如 click / click_image / hotkey / call_code_agent），done 会被拒绝并要求继续。
直接降低“没做完就结束”的失败。
代码：worker.py (line 519)
Tool-calling first + 协议收敛，提高执行确定性
Worker 强制 Anthropic tool-use 分支，走结构化 tool_use/tool_result 循环，而不是自由文本。
解析和控制更稳定。
代码：worker.py (line 44), worker.py (line 456)
工具面做了“可靠性导向”的裁剪与分工
Worker 默认禁用高噪声工具（如 bash/web_search/web_fetch/scholarly），把执行面聚焦到 UI + 代码代理等稳定路径。
同时将点击拆为 click 与 click_image，分别走不同 grounding 路径。
代码：grounding.py (line 191), ui_actions.py (line 138), ui_actions.py (line 169)
记忆机制用于“减少重复探索与遗忘”
任务级状态里有 scratchpad / todo_board / execution_history。
这让单次长链任务里不必反复 OCR/搜索。
代码：grounding.py (line 81), grounding.py (line 152)
上下文工程：只保留必要近端观测，降低注意力稀释
消息 flush 时只保留最近若干图像，避免上下文持续膨胀。
对单次稳定性很关键。
代码：worker.py (line 378)
代码任务下沉到专门的 Code Agent
Worker 可调用 call_code_agent，把“可代码化任务”交给更可控的子循环执行。
降低 GUI 盲操作比例。
代码：motor_code_agent.py (line 669)
一句话对比 Agent-S3 的 BoN：
HIPPO 不是靠“多轨迹外部投票”，而是靠“单轨迹内部的多道质量闸门 + 工具分工 + 记忆与上下文控制”来把 pass@1 做高。


TodoWrite的todoList生成之后，是会在之后的运行过程中被维护吗？我看到有pending  inprogress等状态。最好举个例子向我说明


已处理 53s
会维护，但要区分两件事：

会话内“持久存在”
TodoWrite 写入的是 TodoManager.items，后续轮次还在。
证据：todo.py (line 114), grounding.py (line 158)
不是“自动推进状态”
状态不会自己从 pending -> in_progress -> completed。
必须再次调用 TodoWrite，把新的 items 传进去。
且每次是“整表覆盖”，不是增量 patch。
证据：todo.py (line 54), todo.py (line 114)
另外：

强约束：同一时刻最多一个 in_progress，否则报错。
证据：todo.py (line 111)
Worker 收到 TodoWrite 结果后会继续下一轮推理（把它当上下文更新）。
证据：worker.py (line 596)
一个具体例子（简化）：

第1轮先建 todo
TodoWrite({
  "items": [
    {"id":"1","content":"打开表格","activeForm":"正在打开表格","status":"in_progress"},
    {"id":"2","content":"填写A2","activeForm":"正在填写A2","status":"pending"},
    {"id":"3","content":"核对结果","activeForm":"正在核对结果","status":"pending"}
  ]
})
执行完“打开表格”后，再写一次（手动维护状态）
TodoWrite({
  "items": [
    {"id":"1","content":"打开表格","activeForm":"正在打开表格","status":"completed"},
    {"id":"2","content":"填写A2","activeForm":"正在填写A2","status":"in_progress"},
    {"id":"3","content":"核对结果","activeForm":"正在核对结果","status":"pending"}
  ]
})
执行完“填写A2”后再写
TodoWrite({
  "items": [
    {"id":"1","content":"打开表格","activeForm":"正在打开表格","status":"completed"},
    {"id":"2","content":"填写A2","activeForm":"正在填写A2","status":"completed"},
    {"id":"3","content":"核对结果","activeForm":"正在核对结果","status":"in_progress"}
  ]
})
全部完成后
TodoWrite({
  "items": [
    {"id":"1","content":"打开表格","activeForm":"正在打开表格","status":"completed"},
    {"id":"2","content":"填写A2","activeForm":"正在填写A2","status":"completed"},
    {"id":"3","content":"核对结果","activeForm":"正在核对结果","status":"completed"}
  ]
})
补充一个你可能关心的点：reset_task_state() 目前清了 execution_history/scratchpad，但没有显式清 todo_board。见 grounding.py (line 368)。所以新任务是否“自然清空 todo”取决于是否重新实例化/是否立刻写新 TodoWrite。


也就是说，假设我step1调用了todowrite，step2执行了某内容之后，需要再次调用todowrite来更新todolist？

对，当前实现是这样。

Todo 不会自动根据执行结果改状态；要更新 pending/in_progress/completed，需要在后续 step 再次调用 TodoWrite 并提交更新后的整份 items 列表。
参考：todo.py (line 54), todo.py (line 114)


现在我想复现这个结果，应该使用什么样的bash命令？


已处理 1m 14s
要复现这个 repo 里写的评测流程，直接用它给的 OSWorld 入口脚本命令（在 OSWorld 目录执行）。

参考脚本与文档：

OSWorld.md
run_muscle_mem_agent.py
Worker 强制 Anthropic tool use：worker.py (line 47)
# 1) 准备环境（在 OSWorld 仓库）
conda create -n osworld python=3.10 -y
conda activate osworld
python -m pip install --upgrade pip
python -m pip install -e .

# 2) 安装 HIPPO-Agent（editable）
python -m pip install -e /Users/zhangxiuhui/Desktop/project/HIPPO-Agent

# 3) 复制运行脚本到 OSWorld 根目录
cp /Users/zhangxiuhui/Desktop/project/HIPPO-Agent/osworld_setup/*.py .

# 4)（可选）设置工具 API key
export TAVILY_API_KEY="xxx"
export JINA_API_KEY="xxx"

# 5) 运行评测（SOTA风格配置）
python run_muscle_mem_agent.py \
  --provider_name "aws" \
  --headless \
  --num_envs 4 \
  --max_steps 100 \
  --domain "all" \
  --test_all_meta_path evaluation_examples/test_nogdrive.json \
  --result_dir "results_nogdrive_last_v1" \
  --model_provider "anthropic" \
  --model_url "https://inference.willow.zip" \
  --model "bedrock-opus-4.6" \
  --model_temperature 1.0 \
  --ground_provider "openai" \
  --ground_url "http://localhost:8000/v1" \
  --ground_model "ByteDance-Seed/UI-TARS-1.5-7B" \
  --grounding_width 1920 \
  --grounding_height 1080
# our
python run_local.py \
  --provider_name "docker" \
  --headless \
  --max_steps 100 \
  --domain "all" \
  --test_all_meta_path evaluation_examples/test_small.json \
  --result_dir "results-0302-test" \
  --model_provider "anthropic" \
  --model "bedrock-opus-4.6" \
  --model_temperature 1.0 \
  --ground_provider "openai" \
  --ground_url "http://localhost:8000/v1" \
  --ground_model "ByteDance-Seed/UI-TARS-1.5-7B"\
  --grounding_width 1920 \
  --grounding_height 1080

python run_local_multienv.py \
  --provider_name "docker" \
  --headless \
  --max_steps 100 \
  --domain "all" \
  --test_all_meta_path evaluation_examples/test_nogdrive.json \
  --result_dir "results-0227" \
  --model_provider "anthropic" \
  --model "bedrock-opus-4.6" \
  --model_temperature 1.0 \
  --ground_provider "openai" \
  --ground_url "http://localhost:8000/v1" \
  --ground_model "ByteDance-Seed/UI-TARS-1.5-7B"\
  --grounding_width 1920 \
  --grounding_height 1080 \
  --num_envs 10

# our
python ./bbon/generate_facts.py \
  --results-dirs \
    results-group-0120-origin/results-1/pyautogui/screenshot/gpt-5 \
    results-group-0120-origin/results-2/pyautogui/screenshot/gpt-5 \
    results-group-0120-origin/results-3/pyautogui/screenshot/gpt-5 \
    results-group-0120-origin/results-4/pyautogui/screenshot/gpt-5 \
    results-group-0120-origin/results-5/pyautogui/screenshot/gpt-5 \
  --model "gpt-5" \
  --engine-type "azure" \
  --temperature 1.0

#our 
python ./bbon/run_judge.py \
  --results-dirs \
    results-group-0120-origin/results-1/pyautogui/screenshot/gpt-5 \
    results-group-0120-origin/results-2/pyautogui/screenshot/gpt-5 \
    results-group-0120-origin/results-3/pyautogui/screenshot/gpt-5 \
    results-group-0120-origin/results-5/pyautogui/screenshot/gpt-5 \
  --output-dir "judge-01201517" \
  --examples-path "evaluation_examples/examples" \
  --model "gpt-5" \
  --engine-type "azure" \
  --temperature 1.0

# Step 1: Complete 2 or more rollouts on either AWS or locally
python run.py \
  --provider_name "aws" \
  --headless \
  --num_envs 10 \
  --max_steps 100 \
  --domain "all" \
  --test_all_meta_path evaluation_examples/test_nogdrive.json \
  --result_dir "results" \
  --region "us-east-1" \
  --model_provider "openai" \
  --model "gpt-5-2025-08-07" \
  --model_temperature 1.0 \
  --ground_provider "huggingface" \
  --ground_url "<YOUR_HUGGINGFACE_ENDPOINT_URL>/v1" \
  --grounding_width 1920 \
  --grounding_height 1080 \
  --sleep_after_execution 3

python run_local.py \
  --path_to_vm "/home/zhangxiuhui/projects/OSWorld/docker_vm_data/Ubuntu.qcow2" \
  --provider_name "docker" \
  --headless \
  --max_steps 100 \
  --domain "all" \
  --test_all_meta_path evaluation_examples/test_nogdrive.json \
  --result_dir "results" \
  --model_provider "openai" \
  --model "gpt-5-chat" \
  --model_temperature 1.0 \
  --ground_provider "huggingface" \
  --ground_url "http://localhost:8000/v1" \
  --ground_model "ByteDance-Seed/UI-TARS-1.5-7B"\
  --grounding_width 1920 \
  --grounding_height 1080


# Step 2: Generate Facts
python generate_facts.py \
  --results-dirs \
    results1/pyautogui/screenshot/gpt-5-2025-08-07 \
    results2/pyautogui/screenshot/gpt-5-2025-08-07 \
  --model "gpt-5-2025-08-07" \
  --engine-type "openai" \
  --temperature 1.0



# Step 3: Run the Judge. Make sure the order of the results-dirs is the same as the order above.
python run_judge.py \
  --results-dirs \
    results1/pyautogui/screenshot/gpt-5-2025-08-07 \
    results2/pyautogui/screenshot/gpt-5-2025-08-07 \
  --output-dir "judge_results" \
  --examples-path "evaluation_examples/examples" \
  --model "gpt-5-2025-08-07" \
  --engine-type "openai" \
  --temperature 1.0

#our 
python ./bbon/run_judge.py \
  --results-dirs \
    results1/pyautogui/screenshot/gpt-5-2025-08-07 \
    results2/pyautogui/screenshot/gpt-5-2025-08-07 \
  --output-dir "judge_results" \
  --examples-path "evaluation_examples/examples" \
  --model "gpt-5-2025-08-07" \
  --engine-type "openai" \
  --temperature 1.0