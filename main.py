import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import List
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "github.com/Justmalhar/content-machine.git"

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
OUTPUT_DIR = BASE_DIR / "outputs"
TASKS_FILE = BASE_DIR / "tasks.json"

# Ensure folders exist
formats = [
    "blog",
    "linkedin_article",
    "medium_article",
    "twitter_thread",
    "instagram_carousel",
    "substack_newsletter",
    "youtube_script"
]
for folder in formats:
    (OUTPUT_DIR / folder).mkdir(parents=True, exist_ok=True)

# Models
class BlogPost(BaseModel):
    title: str
    content: str

class SocialPost(BaseModel):
    content: str

class TwitterThread(BaseModel):
    tweets: List[str]

class InstagramCarousel(BaseModel):
    slides: List[str]

# Helpers
def read_prompt(name):
    return (PROMPTS_DIR / name).read_text()

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def timestamp_prefix():
    return datetime.now().strftime("%Y%m%d")

def call_openai(system_prompt, user_input, schema):
    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        text_format=schema
    )
    return response.output_parsed

def set_git_remote():
    if GITHUB_TOKEN:
        new_url = f"https://{GITHUB_TOKEN}@{GITHUB_REPO}"
        subprocess.run(["git", "remote", "set-url", "origin", new_url], check=True)
        print("✅ Git remote updated for token authentication")

# Generation functions
def generate_blog(title):
    return call_openai(read_prompt("blog.md"), f"Write a long-form blog post about: {title}", BlogPost)

def generate_linkedin(blog_content):
    return call_openai(read_prompt("linkedin_article.md"), f"Convert this blog into a LinkedIn article:\n{blog_content}", SocialPost)

def generate_medium(blog_content):
    return call_openai(read_prompt("medium_article.md"), f"Convert this blog into a Medium article:\n{blog_content}", SocialPost)

def generate_twitter(blog_content):
    return call_openai(read_prompt("twitter_thread.md"), f"Convert this blog into a 10-tweet Twitter thread:\n{blog_content}", TwitterThread)

def generate_instagram(blog_content):
    return call_openai(read_prompt("instagram_carousel.md"), f"Convert this blog into an Instagram carousel with 5 slides:\n{blog_content}", InstagramCarousel)

def generate_substack(blog_content):
    return call_openai(read_prompt("substack_newsletter.md"), f"Convert this blog into a Substack newsletter:\n{blog_content}", SocialPost)

def generate_youtube(blog_content):
    return call_openai(read_prompt("youtube_script.md"), f"Convert this blog into a YouTube video script:\n{blog_content}", SocialPost)

def save_output(folder, title, content):
    filename = f"{timestamp_prefix()}-{slugify(title)}.md"
    path = OUTPUT_DIR / folder / filename
    path.write_text(content, encoding="utf-8")
    print(f"✅ Saved {folder}: {path}")

def load_tasks():
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

# GitHub operations
def git_pull_latest():
    try:
        subprocess.run(["git", "fetch", "--all"], check=True)
        subprocess.run(["git", "reset", "--hard", "origin/main"], check=True)
        print("✅ Pulled latest changes from GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git pull failed: {e}")

def git_commit_and_push_task(title):
    try:
        subprocess.run(["git", "add", "."], check=True)
        commit_msg = f"Add generated content for task: {title} ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"✅ Changes for '{title}' pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git push failed for '{title}': {e}")

# Checkpoint system
def mark_checkpoint(task, step):
    checkpoint_file = BASE_DIR / "checkpoint.json"
    with open(checkpoint_file, "w") as f:
        json.dump({"title": task["title"], "step": step}, f)
    print(f"✅ Checkpoint saved: {task['title']} -> {step}")

def clear_checkpoint():
    checkpoint_file = BASE_DIR / "checkpoint.json"
    if checkpoint_file.exists():
        checkpoint_file.unlink()

# Pipeline DAG with parallelization
def run_pipeline(task):
    title = task["title"]
    print(f"🚀 Generating content for: {title}")

    blog = generate_blog(title)
    save_output("blog", title, blog.content)
    mark_checkpoint(task, "blog")

    def linkedin_job():
        save_output("linkedin_article", title, generate_linkedin(blog.content).content)

    def medium_job():
        save_output("medium_article", title, generate_medium(blog.content).content)

    def twitter_job():
        twitter = generate_twitter(blog.content)
        formatted_tweets = [f"### Tweet {i+1}\n\n{tweet}\n" for i, tweet in enumerate(twitter.tweets)]
        save_output("twitter_thread", title, "\n".join(formatted_tweets))

    def instagram_job():
        instagram = generate_instagram(blog.content)
        formatted_slides = [f"### Slide {i+1}\n\n{slide}\n" for i, slide in enumerate(instagram.slides)]
        save_output("instagram_carousel", title, "\n".join(formatted_slides))

    def substack_job():
        save_output("substack_newsletter", title, generate_substack(blog.content).content)

    def youtube_job():
        save_output("youtube_script", title, generate_youtube(blog.content).content)

    jobs = [linkedin_job, medium_job, twitter_job, instagram_job, substack_job, youtube_job]

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(job) for job in jobs]
        for i, future in enumerate(futures, start=1):
            future.result()
            mark_checkpoint(task, f"step_{i}")

    clear_checkpoint()
    print(f"✅ Completed all formats for: {title}")

# Process all tasks and commit after each one
def process_all():
    set_git_remote()
    git_pull_latest()
    tasks = load_tasks()

    for t in tasks:
        if t["status"] == "todo":
            print(f"🚀 Processing: {t['title']}")
            run_pipeline(t)
            t["status"] = "done"
            save_tasks(tasks)  # Save updated status immediately
            git_commit_and_push_task(t["title"])  # Commit and push for this task
            print(f"✅ Task '{t['title']}' processed and pushed to GitHub")

    print("✅ All tasks processed")

if __name__ == "__main__":
    process_all()
