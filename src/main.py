import os
import sys
import math
import jinja2
import markdown
import http.server
import shutil

BASE_URL = os.environ.get("SITEGEN_BASE_URL", "/")

PUBLIC_DIR = "public/"
POSTS_DIR = "posts/"
PAGES_DIR = "pages/"

PAGE_TEMPLATE = "page.html"
POST_TEMPLATE = "post.html"
BLOG_TEMPLATE = "blog.html"

def get_global_format_data() -> dict:
    return {
        "base_url": BASE_URL,
        "get_url": get_url,
        "get_root_url": get_root_url
    }

def render_pages(root_dir: str, templates_env: jinja2.Environment, pages_env: jinja2.Environment):
    print("Reading pages...")
    pages = []

    pages_dir = os.path.join(root_dir, "pages/")
    for path, dirs, files in os.walk(pages_dir):
        for file in files:
            pages.append(file)
            # with open(file_path, "r") as page_file:
            #     page_markdown = page_file.read()
            #     new_page = page.Page(page_markdown)
            #     pages.append(new_page)

    print("Parsing pages...")
    rendered_pages = []
    for page in pages:
        rendered_md = pages_env.get_template(page).render(get_global_format_data())
        rendered_html = markdown.markdown(rendered_md)

        rendered_pages.append((page, rendered_html))

    print("Parsing templates...")
    page_template = templates_env.get_template("page.html")
    templated_pages = []
    for page in rendered_pages:
        page_name, _ = os.path.splitext(page[0])
        rendered_html = page_template.render({
            "page_name": page_name,
            "page_path": page[0],
            "page_html": page[1]
        } | get_global_format_data())
        templated_pages.append((page_name, rendered_html))

    print("Outputing HTML...")
    output_dir = os.path.join(root_dir, "public/")
    for page in templated_pages:
        if page[0] != "index":
            output_path = page[0] + "/index.html"
        else:
            output_path = "index.html"
        output_file_path = os.path.join(output_dir, output_path)
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, "w") as output_file:
            output_file.write(page[1])

class RegenHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def handle(self):
        generate(self.server.site_root_dir)

        os.chdir(self.server.abs_serve_path)

        return super().handle()

def start_server(root_dir: str, serve_path: str):
    generate(root_dir)

    address = ("0.0.0.0", 8080)

    abs_serve_path = os.path.join(root_dir, serve_path)
    os.chdir(abs_serve_path)

    print("Serving {} at {}:{}...".format(serve_path, address[0], address[1]))

    server = http.server.ThreadingHTTPServer(address, RegenHTTPRequestHandler)
    server.site_root_dir = root_dir
    server.abs_serve_path = abs_serve_path
    server.serve_forever()

class Post:
    def __init__(self, abs_file_name: str):
        self.abs_file_name = abs_file_name
        self.rendered_html = ""

    def render(self, env: jinja2.Environment):
        rendered_md = env.get_template(self.get_name()).render(get_global_format_data())
        self.rendered_html = markdown.markdown(rendered_md)

    def get_name(self):
        return os.path.basename(self.abs_file_name)
    
    def get_name_no_ext(self):
        return os.path.splitext(self.get_name())[0]

    def get_html(self):
        return self.rendered_html

    def get_path(self):
        return self.abs_file_name
    
    def get_output_name(self):
        return self.get_name_no_ext()
    
    def get_url(self):
        return BASE_URL + self.get_output_name()
    
def get_url(page_base_name: str) -> str:
    return BASE_URL + page_base_name + "/"

def get_root_url() -> str:
    return BASE_URL
    
def render_post_template(template: jinja2.Template, post: Post) -> str:
    return template.render({
        "post_name": post.get_name(),
        "post_path": post.get_path(),
        "post_html": post.get_html(), 
    } | get_global_format_data()) # here, | combines dictionaries.

def render_blog(root_dir: str, templates_env: jinja2.Environment, posts_env: jinja2.Environment):
    print("Reading posts...")
    posts: list[Post] = []

    posts_dir = os.path.join(root_dir, "posts/")
    for path, dirs, files in os.walk(posts_dir):
        for file in files:
            posts.append(Post(file))

    print("Rendering posts...")
    for post in posts:
        post.render(posts_env)

    print("Parsing templates and outputting...")
    post_template = templates_env.get_template("post.html")
    output_dir = os.path.join(root_dir, "public/")
    for post in posts:
        rendered_html = render_post_template(post_template, post)

        output_path = post.get_name_no_ext() + "/index.html"
        output_file_path = os.path.join(output_dir, output_path)
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        with open(output_file_path, "w") as output_file:
            output_file.write(rendered_html)

    print("Rendering blog...")
    blog_template = templates_env.get_template("blog.html")
    blog_html = blog_template.render({
        "posts": posts
    } | get_global_format_data())
    output_file_path = os.path.join(output_dir, "blog/index.html")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "w") as output_file:
        output_file.write(blog_html)

def clean_output(root_dir: str):
    output_dir = os.path.join(root_dir, "public/")
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)

def copy_resources(root_dir: str):
    shutil.copytree(os.path.join(root_dir, "res"), os.path.join(root_dir, "public/res/"))

def generate(root_dir: str):
    print("Initializing environment...")
    pages_dir = os.path.join(root_dir, "pages/")
    pages_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(pages_dir)
    )

    print("Using SITEGEN_BASE_URL={}...".format(BASE_URL))

    templates_dir = os.path.join(root_dir, "templates/")
    templates_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir)
    )

    posts_dir = os.path.join(root_dir, "posts/")
    posts_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(posts_dir)
    )

    os.chdir(root_dir)

    clean_output(root_dir)

    copy_resources(root_dir)

    render_pages(root_dir, templates_env, pages_env)   

    render_blog(root_dir, templates_env, posts_env)

def main():
    print("Sitegen by gusg21")
    print()

    if len(sys.argv) < 2:
        print("Please specify project root.")
        return
    
    command = "gen"
    if len(sys.argv) >= 3:
        command = sys.argv[2]
    
    root_dir = os.path.abspath(sys.argv[1])

    if "generate".startswith(command):
        generate(root_dir)
    elif "serve".startswith(command):
        start_server(root_dir, "public/")

if __name__ == "__main__":
    main()