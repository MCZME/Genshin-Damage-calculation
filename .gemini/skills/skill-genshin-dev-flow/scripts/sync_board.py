import sys
import subprocess
import json

# 配置信息
PROJECT_OWNER = "MCZME"
PROJECT_NUMBER = 6
STATUS_FIELD_ID = "PVTSSF_lAHOB4dX6s4BOW5Xzg9FWyI"

STATUS_MAPPING = {
    "Backlog": "28b21aa1",
    "Todo": "8f43802f",
    "In Progress": "42d38a7e",
    "Review & GUI Test": "7ef8a5f2",
    "Done": "6cab3f25",
}


def run_command(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    return result.stdout


def sync_issue_to_board(issue_number, target_status):
    if target_status not in STATUS_MAPPING:
        print(f"Invalid status: {target_status}")
        return

    # 1. 获取 Issue 的 URL
    issue_url_raw = run_command(f"gh issue view {issue_number} --json url")
    if not issue_url_raw:
        return
    issue_url = json.loads(issue_url_raw)["url"]

    # 2. 将 Issue 添加到项目并获取 Item ID
    item_add_raw = run_command(
        f"gh project item-add {PROJECT_NUMBER} --owner {PROJECT_OWNER} --url {issue_url} --format json"
    )
    if not item_add_raw:
        return
    item_id = json.loads(item_add_raw)["id"]

    # 3. 更新状态字段
    option_id = STATUS_MAPPING[target_status]
    edit_cmd = (
        f"gh project item-edit --id {item_id} --field-id {STATUS_FIELD_ID} "
        f"--project-id PVT_kwHOB4dX6s4BOW5X --single-select-option-id {option_id}"
    )
    run_command(edit_cmd)
    print(f"Successfully moved Issue #{issue_number} to {target_status}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python sync_board.py <issue_number> <status_name>")
    else:
        sync_issue_to_board(sys.argv[1], sys.argv[2])
