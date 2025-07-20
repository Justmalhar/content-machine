# Content Machine

A script that reads blog titles from `tasks.json`, uses OpenAI to generate a long-form article, then converts it into multiple formats: Instagram carousel, LinkedIn article, Medium article, Substack newsletter, Twitter thread, and YouTube script.

---

## Features

- Read titles and statuses from `tasks.json`  
- Generate blog posts with `prompts/blog.md`  
- Convert that blog into:
  - Instagram carousel (`outputs/instagram_carousel/`)
  - LinkedIn article (`outputs/linkedin_article/`)
  - Medium article (`outputs/medium_article/`)
  - Substack newsletter (`outputs/substack_newsletter/`)
  - Twitter thread (`outputs/twitter_thread/`)
  - YouTube script (`outputs/youtube_script/`)
- Save each format as a Markdown file
- Easy to extend with new formats or prompts

---

## Directory Structure

```
justmalhar-content-machine/
├── README.md
├── LICENSE
├── main.py
├── tasks.json
├── .env.example
├── outputs/
│   ├── blog/
│   │   └── demo.md
│   ├── instagram_carousel/
│   │   └── demo.md
│   ├── linkedin_article/
│   │   └── demo.md
│   ├── medium_article/
│   │   └── demo.md
│   ├── substack_newsletter/
│   │   └── demo.md
│   ├── twitter_thread/
│   │   └── demo.md
│   └── youtube_script/
│       └── demo.md
└── prompts/
    ├── blog.md
    ├── instagram_carousel.md
    ├── linkedin_article.md
    ├── medium_article.md
    ├── substack_newsletter.md
    ├── twitter_thread.md
    └── youtube_script.md
```

---

## Prerequisites

- Python 3.8+  
- OpenAI Python package  
- An OpenAI API key

---

## Installation

1. Clone this repo  
   ```bash
   git clone https://github.com/justmalhar/justmalhar-content-machine.git
   cd justmalhar-content-machine
   ```

2. Create and activate a virtual environment  
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies  
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and set your API key  
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

---

## Configuration

- **.env**
  ```
  OPENAI_API_KEY=your_openai_api_key_here
  ```

- **tasks.json**  
  A list of objects:
  ```json
  [
    { "title": "Why AI Agents Will Replace Traditional Apps", "status": "todo" }
  ]
  ```

- **Prompts**  
  Each file in `prompts/` defines system and user instructions for one format.

---

## Usage

Run the main script:
```bash
python main.py
```

What it does:
1. Reads `tasks.json` for the next "todo" item.
2. Loads the corresponding prompt from `prompts/blog.md`.
3. Generates the blog post and writes it to `outputs/blog/<title>.md`.
4. Uses the blog content as input for each format:
   - Instagram carousel
   - LinkedIn article
   - Medium article
   - Substack newsletter
   - Twitter thread
   - YouTube script
5. Saves each output in its folder under `outputs/`.

---

## Example

After running:
```
outputs/
└── blog/
    └── Why AI Agents Will Replace Traditional Apps.md
└── twitter_thread/
    └── Why AI Agents Will Replace Traditional Apps.md
```

---

## Extending

- Add a new format:
  1. Create a new prompt file in `prompts/`
  2. Update `main.py` to call OpenAI with that prompt
  3. Define an output folder under `outputs/`
- Tweak existing prompts to change tone, length, or style.

---

## License

This project is licensed under the MIT License. See LICENSE for details.

---

## Contact

**Malhar Ujawane** · [@justmalhar](https://twitter.com/justmalhar)  
Staff Software Engineer, Walmart Inc
