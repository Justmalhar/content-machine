import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import List
from concurrent.futures import ThreadPoolExecutor

import requests
from openai import OpenAI
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

# Notion API Setup
NOTION_BASE_URL = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Paths
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = BASE_DIR / "prompts"
OUTPUT_DIR = BASE_DIR / "outputs"

formats = [
    "blog", "linkedin_article", "medium_article",
    "twitter_thread", "instagram_carousel",
    "substack_newsletter", "youtube_script"
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

def save_output(folder, title, content):
    filename = f"{timestamp_prefix()}-{slugify(title)}.md"
    path = OUTPUT_DIR / folder / filename
    path.write_text(content, encoding="utf-8")
    print(f"✅ Saved {folder}: {path}")

# ✅ Fetch tasks from Notion
def fetch_notion_tasks():
    url = f"{NOTION_BASE_URL}/databases/{NOTION_DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Status",
            "select": { "equals": "Not started" }
        }
    }
    r = requests.post(url, headers=HEADERS, json=payload)
    if r.status_code != 200:
        print("❌ Notion API Error:", r.status_code, r.text)
        r.raise_for_status()
    data = r.json()
    tasks = []
    for result in data.get("results", []):
        page_id = result["id"]
        title = result["properties"]["Topic"]["title"][0]["plain_text"]
        tasks.append({"page_id": page_id, "title": title})
    return tasks

def update_notion_status(page_id, status="Done"):
    url = f"{NOTION_BASE_URL}/pages/{page_id}"
    payload = {"properties": {"Status": {"select": {"name": status}}}}
    requests.patch(url, headers=HEADERS, json=payload)

def add_content_to_notion(page_id, section_title, content):
    url = f"{NOTION_BASE_URL}/blocks/{page_id}/children"
    blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": section_title}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": content[:1900]}}]
            }
        }
    ]
    r = requests.patch(url, headers=HEADERS, json={"children": blocks})
    if r.status_code != 200:
        print(f"⚠️ Failed to add content to Notion: {section_title}")
        print(r.text)

# ✅ Content Generators
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

# ✅ Pipeline
def run_pipeline(task):
    title = task["title"]
    page_id = task["page_id"]
    print(f"🚀 Generating content for: {title}")

    # Blog first
    blog = generate_blog(title)
    save_output("blog", title, blog.content)
    add_content_to_notion(page_id, "Blog Post", blog.content)

    def linkedin_job():
        content = generate_linkedin(blog.content).content
        save_output("linkedin_article", title, content)
        add_content_to_notion(page_id, "LinkedIn Article", content)

    def medium_job():
        content = generate_medium(blog.content).content
        save_output("medium_article", title, content)
        add_content_to_notion(page_id, "Medium Article", content)

    def twitter_job():
        twitter = generate_twitter(blog.content)
        tweets = [f"Tweet {i+1}: {t}" for i, t in enumerate(twitter.tweets)]
        content = "\n".join(tweets)
        save_output("twitter_thread", title, content)
        add_content_to_notion(page_id, "Twitter Thread", content)

    def instagram_job():
        instagram = generate_instagram(blog.content)
        slides = [f"Slide {i+1}: {s}" for i, s in enumerate(instagram.slides)]
        content = "\n".join(slides)
        save_output("instagram_carousel", title, content)
        add_content_to_notion(page_id, "Instagram Carousel", content)

    def substack_job():
        content = generate_substack(blog.content).content
        save_output("substack_newsletter", title, content)
        add_content_to_notion(page_id, "Substack Newsletter", content)

    def youtube_job():
        content = generate_youtube(blog.content).content
        save_output("youtube_script", title, content)
        add_content_to_notion(page_id, "YouTube Script", content)

    # Parallel execution
    jobs = [linkedin_job, medium_job, twitter_job, instagram_job, substack_job, youtube_job]
    with ThreadPoolExecutor(max_workers=6) as executor:
        [executor.submit(job) for job in jobs]

    update_notion_status(page_id, "Done")
    print(f"✅ Completed all formats for: {title}")

# ✅ Main
def process_all():
    tasks = fetch_notion_tasks()
    if not tasks:
        print("✅ No pending tasks in Notion.")
        return
    for task in tasks:
        run_pipeline(task)

if __name__ == "__main__":
    process_all()
