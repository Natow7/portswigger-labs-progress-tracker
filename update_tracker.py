"""
PortSwigger Labs Progress Tracker - Auto Updater (v3 - self-managed categories)

Usage:
    python update_tracker.py

Run this from inside your repo folder (where README.md lives).

Categories, difficulties, and the overall lab total now live in
tracker_config.json (created automatically next to README.md the first
time you run this). Use the "Manage topics/categories" option to add
new topics without ever touching this script's code again.
"""

import json
import os
import re
import subprocess
from datetime import date

README = "README.md"
CONFIG_FILE = "tracker_config.json"

DEFAULT_CONFIG = {
    "difficulties": {"Apprentice": 61, "Practitioner": 174, "Expert": 39},
    "categories": {
        "Authentication vulnerabilities": 14,
        "SQL injection": 18,
        "Access control": 13,
        "Path traversal": 6,
        "Command injection": 5,
    },
    "total_labs": 285,
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"No {CONFIG_FILE} found — creating one with your current categories/difficulties.")
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def as_menu(names):
    """Turn a list of names into a {'1': name, '2': name, ...} menu dict, in insertion order."""
    return {str(i + 1): name for i, name in enumerate(names)}


def read_file():
    with open(README, "r", encoding="utf-8") as f:
        return f.read()


def write_file(content):
    with open(README, "w", encoding="utf-8") as f:
        f.write(content)


def prompt_choice(prompt, options):
    print(prompt)
    for key, val in options.items():
        print(f"  {key}. {val}")
    while True:
        choice = input("Enter number: ").strip()
        if choice in options:
            return options[choice]
        print("Invalid choice, try again.")


def classify_git_error(label, stderr):
    """
    Look at stderr from a failed git command and return a
    (description, recommendation, autofix_cmd_or_None) tuple.
    autofix_cmd, if present, is a command that might resolve the issue,
    which we'll only ever run after the user confirms.
    """
    text = stderr.lower()

    if "not a git repository" in text:
        return (
            "This folder isn't a git repository (or you're not inside it).",
            "cd into your actual repo folder (the one containing README.md and a .git folder), then run this script again.",
            None,
        )

    if "no configured push destination" in text or "does not appear to be a git repository" in text:
        return (
            "No remote named 'origin' is configured for this repo.",
            "Set it up with: git remote add origin <your-repo-url>",
            None,
        )

    if "could not read username" in text or "authentication failed" in text or "permission denied (publickey)" in text or "403" in text:
        return (
            "GitHub rejected your credentials (login or SSH key issue).",
            "If using HTTPS: set up a personal access token (GitHub no longer accepts plain passwords). "
            "If using SSH: check your key is added with `ssh-add` and registered on GitHub.",
            None,
        )

    if "could not resolve host" in text or "network is unreachable" in text or "timed out" in text:
        return (
            "Couldn't reach GitHub — looks like a network/connectivity problem.",
            "Check your internet connection and try again.",
            None,
        )

    if "failed to push some refs" in text or ("updates were rejected" in text and "non-fast-forward" in text):
        return (
            "Your local branch is behind the remote — someone/something pushed changes you don't have locally.",
            "Pull the remote changes first (rebasing your commit on top), then push again.",
            ["git", "pull", "--rebase", "origin", "main"],
        )

    if "divergent branches" in text or "need to specify how to reconcile" in text:
        return (
            "Your local and remote branches have diverged (both have commits the other doesn't).",
            "Rebase your local commit on top of the remote's, then push again.",
            ["git", "pull", "--rebase", "origin", "main"],
        )

    if "could not apply" in text and "rebase" in text:
        return (
            "The rebase hit a real conflict — README.md was changed differently on both sides and git can't merge them automatically.",
            "Open README.md, resolve the <<<<<<< / ======= / >>>>>>> conflict markers by hand, then run: "
            "git add README.md && git rebase --continue && git push origin main. "
            "(Or run `git rebase --abort` to cancel and go back to how things were.)",
            None,
        )

    if "you are not currently on a branch" in text or "detached head" in text:
        return (
            "You're in a 'detached HEAD' state, not on a real branch — commits here won't attach to 'main'.",
            "Run `git checkout main` first, then run this script again.",
            None,
        )

    if "please commit your changes or stash them" in text or ("cannot pull with rebase" in text and "unstaged" in text):
        return (
            "You have other uncommitted changes in the repo that would get overwritten by pulling/rebasing.",
            "Either commit those changes separately first, or stash them with `git stash`, then run this script again.",
            None,
        )

    if "refusing to merge unrelated histories" in text:
        return (
            "The local and remote repos don't share a common history (often happens on a freshly re-initialized repo).",
            "If this is expected, run: git pull --rebase --allow-unrelated-histories origin main. "
            "If it's unexpected, double check you're pointed at the right remote with `git remote -v`.",
            None,
        )

    if "unmerged paths" in text or "conflict" in text:
        return (
            "There's a merge conflict that needs to be resolved manually.",
            "Open README.md, resolve the conflict markers (<<<<<<< / ======= / >>>>>>>), "
            "then run: git add README.md && git commit && git push origin main",
            None,
        )

    if "nothing to commit" in text:
        return (
            "Git says there's nothing new to commit — README.md may not have actually changed.",
            "Check `git status` and `git diff README.md` to confirm the file was updated as expected.",
            None,
        )

    if "protected branch" in text or "hook declined" in text:
        return (
            "The 'main' branch is protected and rejected this push directly.",
            "Push to a new branch and open a pull request instead: "
            "git push origin HEAD:update-tracker",
            None,
        )

    if "src refspec main does not match any" in text:
        return (
            "There's no local branch named 'main' to push (your default branch may be called something else, e.g. 'master').",
            "Check your branch name with `git branch` and adjust the push command accordingly.",
            None,
        )

    # Fallback: unrecognized error
    return (
        f"'{label}' failed with an error git didn't give us a recognized pattern for.",
        "Read the raw error below and search it, or run the commands manually to investigate.",
        None,
    )


def run_git_push(commit_msg):
    """Stage README.md and the config file, commit, and push. Returns True on full success."""
    steps = [
        (["git", "add", README, CONFIG_FILE], "git add"),
        (["git", "commit", "-m", commit_msg], "git commit"),
        (["git", "push", "origin", "main"], "git push"),
    ]

    i = 0
    while i < len(steps):
        cmd, label = steps[i]
        print(f"\n$ {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            print("Problem:        'git' isn't installed, or isn't on your PATH.")
            print("Recommendation: Install git (https://git-scm.com/downloads) and make sure the "
                  "`git` command works in a plain terminal before rerunning this script.")
            return False

        if result.stdout.strip():
            print(result.stdout.strip())

        if result.returncode == 0:
            i += 1
            continue

        if label == "git commit" and "nothing to commit" in result.stderr.lower() + result.stdout.lower():
            print("\nNothing new to commit (files didn't actually change) — skipping straight to push.")
            i += 1
            continue

        description, recommendation, autofix_cmd = classify_git_error(label, result.stderr)
        print(f"\n'{label}' failed.")
        print(f"Problem:        {description}")
        print(f"Recommendation: {recommendation}")
        print(f"\nRaw git error:\n{result.stderr.strip()}")

        if autofix_cmd:
            answer = input(
                f"\nWant me to try running `{' '.join(autofix_cmd)}` to fix this, then retry the push? (y/N): "
            ).strip().lower()
            if answer == "y":
                print(f"\n$ {' '.join(autofix_cmd)}")
                fix_result = subprocess.run(autofix_cmd, capture_output=True, text=True)
                if fix_result.stdout.strip():
                    print(fix_result.stdout.strip())
                if fix_result.returncode != 0:
                    fix_desc, fix_rec, _ = classify_git_error(" ".join(autofix_cmd), fix_result.stderr)
                    print(f"\n'{' '.join(autofix_cmd)}' also failed.")
                    print(f"Problem:        {fix_desc}")
                    print(f"Recommendation: {fix_rec}")
                    print(f"\nRaw git error:\n{fix_result.stderr.strip()}")
                    print("\nStopping here — please resolve this manually, then rerun the script or push by hand.")
                    return False
                print("Fix applied. Retrying the push...")
                continue  # retry the same step (git push) without advancing i
            else:
                print("\nOkay, not auto-fixing. Stopping here — you can finish manually.")
                return False
        else:
            print("\nStopping here — you can finish manually once the issue above is resolved.")
            return False

    return True


def push_flow(commit_msg):
    answer = input("\nPush this update to GitHub now? (y/N): ").strip().lower()
    if answer == "y":
        success = run_git_push(commit_msg)
        if success:
            print("\nPushed to GitHub successfully!")
    else:
        print("\nSkipped push. Run these when you're ready:")
        print(f'   git add {README} {CONFIG_FILE}')
        print(f'   git commit -m "{commit_msg}"')
        print('   git push origin main')


def confirm_and_apply(content, pattern, replacement, label, old_display, new_display):
    """Show old -> new, ask for confirmation, and apply the regex substitution if confirmed."""
    print(f"\n{label}")
    print(f"  Current: {old_display}")
    print(f"  New:     {new_display}")
    answer = input("Apply this change? (y/N): ").strip().lower()
    if answer != "y":
        print("Skipped.")
        return content, False
    new_content = pattern.sub(replacement, content, count=1)
    return new_content, True


def repair_badges(content):
    choice = prompt_choice(
        "Which badge do you want to fix?",
        {
            "1": "Total Labs Solved",
            "2": "Last Updated",
            "3": "Completed %",
            "4": "Back",
        },
    )
    if choice == "Back":
        return content

    if choice == "Total Labs Solved":
        pattern = re.compile(r"(Total%20Labs%20Solved-)(\d+)(-blue)")
        m = pattern.search(content)
        if not m:
            print("Couldn't find this badge in README.md — no changes made.")
            return content
        new_val = input(f"New total solved count (currently {m.group(2)}): ").strip()
        if not new_val.isdigit():
            print("That's not a whole number — no changes made.")
            return content
        content, _ = confirm_and_apply(
            content, pattern, rf"\g<1>{new_val}\g<3>",
            "Total Labs Solved badge", m.group(2), new_val,
        )
        return content

    if choice == "Last Updated":
        pattern = re.compile(r"(Last%20Updated-)([\d-]+)(-yellow)")
        m = pattern.search(content)
        if not m:
            print("Couldn't find this badge in README.md — no changes made.")
            return content
        new_val = input("New date (YYYY-MM-DD): ").strip()
        try:
            date.fromisoformat(new_val)
        except ValueError:
            print("That's not a valid date in YYYY-MM-DD format — no changes made.")
            return content
        badge_val = new_val.replace("-", "--")
        content, _ = confirm_and_apply(
            content, pattern, rf"\g<1>{badge_val}\g<3>",
            "Last Updated badge", m.group(2), badge_val,
        )
        return content

    if choice == "Completed %":
        pattern = re.compile(r"(Completed-)([\d.]+)(%25-purple)")
        m = pattern.search(content)
        if not m:
            print("Couldn't find this badge in README.md — no changes made.")
            return content
        new_val = input(f"New completion % (currently {m.group(2)}), just the number: ").strip()
        try:
            float(new_val)
        except ValueError:
            print("That's not a valid number — no changes made.")
            return content
        content, _ = confirm_and_apply(
            content, pattern, rf"\g<1>{new_val}\g<3>",
            "Completed % badge", m.group(2), new_val,
        )
        return content

    return content


def repair_counters(content, config):
    choice = prompt_choice(
        "Which counter do you want to fix?",
        {"1": "Difficulty counter", "2": "Category counter", "3": "Back"},
    )
    if choice == "Back":
        return content

    if choice == "Difficulty counter":
        diff_map = config["difficulties"]
        difficulty = prompt_choice("Which difficulty?", as_menu(list(diff_map.keys())))
        pattern = re.compile(rf"\*\*{re.escape(difficulty)}\*\*:\s*(\d+)\s*of\s*{diff_map[difficulty]}")
        m = pattern.search(content)
        if not m:
            print(f"Couldn't find the {difficulty} counter in README.md — no changes made.")
            return content
        new_val = input(f"New count for {difficulty} (currently {m.group(1)} of {diff_map[difficulty]}): ").strip()
        if not new_val.isdigit():
            print("That's not a whole number — no changes made.")
            return content
        content, _ = confirm_and_apply(
            content, pattern, f"**{difficulty}**: {new_val} of {diff_map[difficulty]}",
            f"{difficulty} counter", f"{m.group(1)} of {diff_map[difficulty]}", f"{new_val} of {diff_map[difficulty]}",
        )
        return content

    if choice == "Category counter":
        cat_map = config["categories"]
        topic = prompt_choice("Which category?", as_menu(list(cat_map.keys())))
        pattern = re.compile(rf"\*\*{re.escape(topic)}\*\*:\s*(\d+)/{cat_map[topic]}\s*lab")
        m = pattern.search(content)
        if not m:
            print(f"Couldn't find the {topic} counter in README.md — no changes made.")
            return content
        new_val = input(f"New count for {topic} (currently {m.group(1)}/{cat_map[topic]}): ").strip()
        if not new_val.isdigit():
            print("That's not a whole number — no changes made.")
            return content
        content, _ = confirm_and_apply(
            content, pattern, f"**{topic}**: {new_val}/{cat_map[topic]} lab",
            f"{topic} counter", f"{m.group(1)}/{cat_map[topic]}", f"{new_val}/{cat_map[topic]}",
        )
        return content

    return content


def repair_table_row(content):
    row_num = input("Row number to edit: ").strip()
    if not row_num.isdigit():
        print("That's not a valid row number — no changes made.")
        return content

    row_pattern = re.compile(rf"^\|\s*{row_num}\s*\|(.*)\|$", re.MULTILINE)
    m = row_pattern.search(content)
    if not m:
        print(f"Couldn't find row {row_num} in the table — no changes made.")
        return content

    fields = [f.strip() for f in m.group(1).split("|")]
    if len(fields) != 5:
        print("This row doesn't look like the expected 5-column format (date/topic/title/difficulty/writeup).")
        print(f"Raw row content: {m.group(0)}")
        print("Edit it manually in README.md instead — skipping to avoid corrupting the table.")
        return content

    field_names = ["Date", "Topic", "Lab title", "Difficulty", "Writeup"]
    print(f"\nCurrent row {row_num}:")
    for name, val in zip(field_names, fields):
        print(f"  {name}: {val}")

    print("\nEnter new values (press Enter to keep the current value):")
    new_fields = []
    for name, val in zip(field_names, fields):
        new_val = input(f"  {name} [{val}]: ").strip()
        new_fields.append(new_val if new_val else val)

    new_row = f"| {row_num} | " + " | ".join(new_fields) + " |"
    print(f"\nNew row {row_num}:")
    for name, val in zip(field_names, new_fields):
        print(f"  {name}: {val}")
    answer = input("Apply this change? (y/N): ").strip().lower()
    if answer != "y":
        print("Skipped.")
        return content

    content = row_pattern.sub(new_row.replace("\\", "\\\\"), content, count=1)
    return content


def add_new_category(content, config):
    """Add a brand new topic/category: update config, and optionally insert its
    counter line into the README, all with confirmation before writing anything."""
    print("\nAdd a new topic/category")
    name = input("Topic name (exactly as you want it displayed): ").strip()
    if not name:
        print("Empty name — cancelled.")
        return content, config

    if name in config["categories"]:
        print(f"'{name}' already exists with {config['categories'][name]} labs — use 'Fix a counter' instead if you need to change its total.")
        return content, config

    total_str = input(f"How many labs are in '{name}'?: ").strip()
    if not total_str.isdigit() or int(total_str) <= 0:
        print("That's not a valid positive number — cancelled.")
        return content, config
    total = int(total_str)

    print(f"\nAbout to add category: '{name}' with {total} labs.")
    print(f"This will also raise the overall lab total used for the Completed % badge "
          f"from {config['total_labs']} to {config['total_labs'] + total}.")
    answer = input("Proceed? (y/N): ").strip().lower()
    if answer != "y":
        print("Cancelled — no changes made.")
        return content, config

    config["categories"][name] = total
    config["total_labs"] += total
    save_config(config)
    print(f"Saved to {CONFIG_FILE}.")

    # Offer to also insert a matching counter line into the README
    existing_counters = list(re.finditer(r"^\*\*.+\*\*:\s*\d+/\d+\s*lab.*$", content, re.MULTILINE))
    new_line = f"**{name}**: 0/{total} lab"
    if existing_counters:
        preview_after = existing_counters[-1].group(0)
        print(f"\nI can insert this line into README.md right after your last category counter:")
        print(f"  ...after: {preview_after}")
        print(f"  new line: {new_line}")
        answer = input("Insert it there? (y/N): ").strip().lower()
        if answer == "y":
            insert_pos = existing_counters[-1].end()
            content = content[:insert_pos] + "\n" + new_line + content[insert_pos:]
            print("Inserted.")
        else:
            print(f"Skipped — you'll need to add this line to README.md yourself:\n  {new_line}")
    else:
        print(f"\nCouldn't find any existing '**Category**: X/Y lab' lines to insert after.")
        print(f"Add this line to README.md yourself wherever your category counters live:\n  {new_line}")

    return content, config


def repair_mode(content, config):
    while True:
        choice = prompt_choice(
            "What do you want to fix or manage?",
            {
                "1": "A badge (Total Solved / Last Updated / Completed %)",
                "2": "A difficulty or category counter",
                "3": "A specific table row",
                "4": "Add a new topic/category",
                "5": "Done — save and exit repair mode",
            },
        )
        if choice.startswith("A badge"):
            content = repair_badges(content)
        elif choice.startswith("A difficulty"):
            content = repair_counters(content, config)
        elif choice.startswith("A specific"):
            content = repair_table_row(content)
        elif choice.startswith("Add a new"):
            content, config = add_new_category(content, config)
        else:
            return content, config


def ensure_difficulty_counter(content, difficulty, diff_map):
    """Make sure a '**Difficulty**: X of Y' line exists. Offers to insert a
    starting '0 of Y' line if missing. Returns (content, ok)."""
    pattern = re.compile(rf"\*\*{re.escape(difficulty)}\*\*:\s*(\d+)\s*of\s*{diff_map[difficulty]}")
    if pattern.search(content):
        return content, True

    print(f"\nProblem: No '{difficulty}' difficulty counter found in README.md "
          f"(expected a line like '**{difficulty}**: X of {diff_map[difficulty]}').")
    anchors = list(re.finditer(r"^\*\*.+\*\*:\s*\d+\s*of\s*\d+.*$", content, re.MULTILINE))
    new_line = f"**{difficulty}**: 0 of {diff_map[difficulty]}"
    if anchors:
        print("Recommendation: insert a starting line right after your last difficulty counter:")
        print(f"  ...after: {anchors[-1].group(0)}")
        print(f"  new line: {new_line}")
        answer = input("Insert it now and continue? (y/N): ").strip().lower()
        if answer == "y":
            pos = anchors[-1].end()
            content = content[:pos] + "\n" + new_line + content[pos:]
            print("Inserted.")
            return content, True
    else:
        print(f"Recommendation: add this line to README.md yourself, then run the script again:\n  {new_line}")
    return content, False


def ensure_category_counter(content, topic, cat_map):
    """Make sure a '**Topic**: X/Y lab' line exists. Offers to insert a
    starting '0/Y lab' line if missing. Returns (content, ok)."""
    pattern = re.compile(rf"\*\*{re.escape(topic)}\*\*:\s*(\d+)/{cat_map[topic]}\s*lab")
    if pattern.search(content):
        return content, True

    print(f"\nProblem: No '{topic}' category counter found in README.md "
          f"(expected a line like '**{topic}**: X/{cat_map[topic]} lab').")
    anchors = list(re.finditer(r"^\*\*.+\*\*:\s*\d+/\d+\s*lab.*$", content, re.MULTILINE))
    new_line = f"**{topic}**: 0/{cat_map[topic]} lab"
    if anchors:
        print("Recommendation: insert a starting line right after your last category counter:")
        print(f"  ...after: {anchors[-1].group(0)}")
        print(f"  new line: {new_line}")
        answer = input("Insert it now and continue? (y/N): ").strip().lower()
        if answer == "y":
            pos = anchors[-1].end()
            content = content[:pos] + "\n" + new_line + content[pos:]
            print("Inserted.")
            return content, True
    else:
        print(f"Recommendation: add this line to README.md yourself, then run the script again:\n  {new_line}")
    return content, False


def ensure_badge(content, pattern, badge_name, expected_format_hint):
    """Badges aren't safely auto-insertable (unknown surrounding markdown), so
    we just report clearly and let the caller abort."""
    if pattern.search(content):
        return True
    print(f"\nProblem: Couldn't find the '{badge_name}' badge in README.md.")
    print(f"Recommendation: make sure it exists in this format, then run the script again:\n  {expected_format_hint}")
    return False


def main():
    config = load_config()
    content = read_file()
    today = date.today().isoformat()

    mode = prompt_choice(
        "Entry type:",
        {
            "1": "Full entry (adds a row to the table)",
            "2": "Quick count (just bump the numbers, no table row)",
            "3": "Repair / manage mode (fix a badge, counter, row, or add a new topic)",
        },
    )

    if mode.startswith("Repair"):
        content, config = repair_mode(content, config)
        write_file(content)
        print("\nREADME.md updated (repair/manage mode).")
        commit_msg = input("Commit message (Enter for default 'Fix: sync README counters/badges'): ").strip()
        if not commit_msg:
            commit_msg = "Fix: sync README counters/badges"
        push_flow(commit_msg)
        return

    quick_mode = mode.startswith("Quick")

    lab_title = None
    writeup = None
    if not quick_mode:
        lab_title = input("Exact lab title (from PortSwigger): ").strip()

    topic = prompt_choice("Topic/category:", as_menu(list(config["categories"].keys())))
    difficulty = prompt_choice("Difficulty:", as_menu(list(config["difficulties"].keys())))

    if not quick_mode:
        writeup = input("Writeup link (press Enter for N/A): ").strip() or "N/A"

    # --- Pre-flight validation: check EVERYTHING exists before changing ANYTHING.
    # This prevents the bug where some counters get incremented and others don't,
    # which would silently corrupt the numbers if you ran the script again.
    diff_map = config["difficulties"]
    cat_map = config["categories"]

    content, diff_ok = ensure_difficulty_counter(content, difficulty, diff_map)
    content, cat_ok = ensure_category_counter(content, topic, cat_map)

    total_pattern = re.compile(r"(Total%20Labs%20Solved-)(\d+)(-blue)")
    total_ok = ensure_badge(
        content, total_pattern, "Total Labs Solved",
        "![...](https://img.shields.io/badge/Total%20Labs%20Solved-N-blue)",
    )
    last_updated_pattern = re.compile(r"(Last%20Updated-)([\d-]+)(-yellow)")
    last_updated_ok = ensure_badge(
        content, last_updated_pattern, "Last Updated",
        "![...](https://img.shields.io/badge/Last%20Updated-YYYY--MM--DD-yellow)",
    )
    completed_pattern = re.compile(r"(Completed-)([\d.]+)(%25-purple)")
    completed_ok = ensure_badge(
        content, completed_pattern, "Completed %",
        "![...](https://img.shields.io/badge/Completed-X-purple)",
    )

    if not (diff_ok and cat_ok and total_ok and last_updated_ok and completed_ok):
        print("\nAborting — nothing was changed in README.md, and nothing was committed.")
        print("Fix the issue(s) above (or say yes to the offered auto-insert next time), then run the script again.")
        return

    # --- Everything checks out — now it's safe to make changes ---

    if not quick_mode:
        # --- Find next empty placeholder row (Date == 2026-00-00) ---
        row_pattern = re.compile(
            r"^\|\s*(\d+)\s*\|\s*2026-00-00\s*\|.*\|\s*N/A\s*\|$", re.MULTILINE
        )
        matches = row_pattern.findall(content)

        if matches:
            row_num = matches[0]
            new_row = (
                f"| {row_num} | {today} | {topic} | {lab_title} | {difficulty} | {writeup} |"
            )
            old_row_pattern = re.compile(
                rf"^\|\s*{row_num}\s*\|\s*2026-00-00\s*\|.*\|\s*N/A\s*\|$", re.MULTILINE
            )
            content = old_row_pattern.sub(new_row, content, count=1)
        else:
            rows = re.findall(r"^\|\s*(\d+)\s*\|.*\|$", content, re.MULTILINE)
            next_num = int(rows[-1]) + 1 if rows else 1
            new_row = f"| {next_num} | {today} | {topic} | {lab_title} | {difficulty} | {writeup} |"
            last_row_match = list(re.finditer(r"^\|\s*\d+\s*\|.*\|$", content, re.MULTILINE))[-1]
            insert_pos = last_row_match.end()
            content = content[:insert_pos] + "\n" + new_row + content[insert_pos:]

    # --- Update difficulty counter (guaranteed to match — validated above) ---
    diff_pattern = re.compile(rf"\*\*{re.escape(difficulty)}\*\*:\s*(\d+)\s*of\s*{diff_map[difficulty]}")
    m = diff_pattern.search(content)
    new_count = int(m.group(1)) + 1
    content = diff_pattern.sub(f"**{difficulty}**: {new_count} of {diff_map[difficulty]}", content)

    # --- Update category counter (guaranteed to match — validated above) ---
    cat_pattern = re.compile(rf"\*\*{re.escape(topic)}\*\*:\s*(\d+)/{cat_map[topic]}\s*lab")
    m = cat_pattern.search(content)
    new_count = int(m.group(1)) + 1
    content = cat_pattern.sub(f"**{topic}**: {new_count}/{cat_map[topic]} lab", content)

    # --- Update Total Labs Solved badge (guaranteed to match — validated above) ---
    m = total_pattern.search(content)
    total_solved = int(m.group(2)) + 1
    content = total_pattern.sub(rf"\g<1>{total_solved}\g<3>", content)

    # --- Update Last Updated badge (guaranteed to match — validated above) ---
    today_badge = today.replace("-", "--")
    content = last_updated_pattern.sub(rf"\g<1>{today_badge}\g<3>", content)

    # --- Update Completed % badge (guaranteed to match — validated above) ---
    total_labs = config["total_labs"]
    pct = round((total_solved / total_labs) * 100, 1) if total_labs else 0
    pct_str = f"{pct}".rstrip("0").rstrip(".") if "." in f"{pct}" else f"{pct}"
    if pct_str == "":
        pct_str = "0"
    content = completed_pattern.sub(rf"\g<1>{pct_str}\g<3>", content)

    write_file(content)
    print("\nREADME.md updated successfully!")
    if quick_mode:
        print(f"   Counted: {topic}, {difficulty} (no table row added)")
        commit_msg = f"Progress: +1 {topic} ({difficulty})"
    else:
        print(f"   Added: {lab_title} ({topic}, {difficulty})")
        commit_msg = f"Completed: {lab_title}"
    print(f"   Total solved: {total_solved}/{total_labs} ({pct_str}%)")

    push_flow(commit_msg)


if __name__ == "__main__":
    main()
