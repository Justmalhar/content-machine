import os
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from pydantic import BaseModel

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
OUTPUT_DIR = BASE_DIR / "outputs"
TASKS_FILE = BASE_DIR / "tasks.json"

# Create folders if they don't exist
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
    tweets: list[str]

class InstagramCarousel(BaseModel):
    slides: list[str]

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

# Save outputs
def save_output(folder, title, content):
    filename = f"{timestamp_prefix()}-{slugify(title)}.md"
    path = OUTPUT_DIR / folder / filename
    path.write_text(content, encoding="utf-8")
    print(f"✅ Saved {folder}: {path}")

# Load & save tasks
def load_tasks():
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

# GitHub integration
def git_commit_and_push():
    try:
        subprocess.run(["git", "add", "."], check=True)
        commit_msg = f"Auto-update content {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Changes pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")

# Pipeline DAG
def run_pipeline(title):
    print(f"🚀 Generating content for: {title}")

    blog = generate_blog(title)
    save_output("blog", title, blog.content)

    linkedin = generate_linkedin(blog.content)
    save_output("linkedin_article", title, linkedin.content)

    medium = generate_medium(blog.content)
    save_output("medium_article", title, medium.content)

    twitter = generate_twitter(blog.content)
    save_output("twitter_thread", title, "\n".join(twitter.tweets))

    instagram = generate_instagram(blog.content)
    save_output("instagram_carousel", title, "\n---\n".join(instagram.slides))

    substack = generate_substack(blog.content)
    save_output("substack_newsletter", title, substack.content)

    youtube = generate_youtube(blog.content)
    save_output("youtube_script", title, youtube.content)

    print(f"✅ Completed all formats for: {title}")

# Process next task
def process_next():
    tasks = load_tasks()
    for t in tasks:
        if t["status"] == "todo":
            run_pipeline(t["title"])
            t["status"] = "done"
            save_tasks(tasks)
            git_commit_and_push()
            return
    print("✅ No pending tasks")

if __name__ == "__main__":
    process_next()
