import subprocess
import json


def run_command(command):
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr.strip()}"


def get_git_status():
    branch = run_command("git rev-parse --abbrev-ref HEAD")
    # 修复之前格式化字符串的问题
    last_commit = run_command('git log -1 --pretty=format:"%h - %s (%cr)"')
    status = run_command("git status --short")
    return {
        "branch": branch,
        "last_commit": last_commit,
        "pending_changes": status if status else "Clean",
    }


def get_github_issues(assignee=None):
    assignee_flag = f"--assignee {assignee}" if assignee else ""
    cmd = f"gh issue list {assignee_flag} --state open --json number,title,milestone,labels"
    result = run_command(cmd)
    if result.startswith("Error") or not result:
        return result
    try:
        issues = json.loads(result)
        if not issues:
            return ""
        return "".join(
            [
                f"- [#{i['number']}] {i['title']} (Milestone: {i['milestone']['title'] if i['milestone'] else 'None'})\n"
                for i in issues
            ]
        )
    except:
        return "Error parsing issues."


def get_github_prs():
    cmd = "gh pr list --author @me --state open --json number,title,state"
    result = run_command(cmd)
    if result.startswith("Error") or not result:
        return result
    try:
        prs = json.loads(result)
        return "".join(
            [f"- [!{p['number']}] {p['title']} ({p['state']})\n" for p in prs]
        )
    except:
        return "Error parsing PRs."


def get_milestones():
    # 使用 API 获取，因为 gh milestone 可能不可用
    cmd = 'gh api repos/:owner/:repo/milestones --jq ".[] | {title: .title, open_issues: .open_issues, closed_issues: .closed_issues}"'
    result = run_command(cmd)
    if result.startswith("Error") or not result:
        return result
    try:
        # gh api 返回的是多行 JSON 对象字符串
        lines = result.splitlines()
        formatted = ""
        for line in lines:
            m = json.loads(line)
            formatted += f"- {m['title']} (Open: {m['open_issues']}, Closed: {m['closed_issues']})\n"
        return formatted
    except:
        return "Error parsing milestones."


def main():
    print("--- 🛡️ Genshin Dev Flow Context Report 🛡️ ---\n")

    print("## 1. 📍 Local Git Context")
    git_info = get_git_status()
    print(f"* **Branch:** {git_info['branch']}")
    print(f"* **Last Commit:** {git_info['last_commit']}")
    print(f"* **Status:**\n{git_info['pending_changes']}\n")

    print("## 2. 🎯 Active Milestones")
    print(get_milestones() or "* No active milestones.\n")

    print("## 3. 🐙 Assigned Issues (@me)")
    assigned = get_github_issues(assignee="@me")
    print(assigned if assigned else "* No open issues assigned to you.\n")

    print("## 4. 🌐 All Open Issues")
    all_issues = get_github_issues()
    print(all_issues if all_issues else "* No open issues found.\n")

    print("## 5. 🔀 Active Pull Requests")
    prs = get_github_prs()
    print(prs if prs else "* No active PRs.\n")

    print("✅ Context loaded. Ready to execute.")


if __name__ == "__main__":
    main()
