# our
python run_local.py \
  --provider_name "docker" \
  --headless \
  --max_steps 100 \
  --domain "all" \
  --test_all_meta_path evaluation_examples/test_small.json \
  --result_dir "results-0114-test" \
  --model_provider "azure" \
  --model "gpt-5" \
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
  --result_dir "results-01201005" \
  --model_provider "azure" \
  --model "gpt-5" \
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