import os
import sys
import math
import jinja2
import markdown
import http.server

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
        rendered_md = pages_env.get_template(page).render()
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
        })
        templated_pages.append((page_name, rendered_html))

    print("Outputing HTML...")
    output_dir = os.path.join(root_dir, "public/")
    for page in templated_pages:
        output_file_path = os.path.join(output_dir, page[0] + ".html")
        with open(output_file_path, "w") as output_file:
            output_file.write(page[1])

class RegenHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def handle(self):
        generate(self.server.site_root_dir)

        return super().handle()

def start_server(root_dir: str, serve_path: str):
    address = ("0.0.0.0", 8080)

    abs_serve_path = os.path.join(root_dir, serve_path)
    os.chdir(abs_serve_path)

    print("Serving {} at {}:{}...".format(serve_path, address[0], address[1]))

    server = http.server.ThreadingHTTPServer(address, RegenHTTPRequestHandler)
    server.site_root_dir = root_dir
    server.serve_forever()

def generate(root_dir: str):
    print("Initializing environment...")
    pages_dir = os.path.join(root_dir, "pages/")
    templates_dir = os.path.join(root_dir, "templates/")
    pages_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(pages_dir)
    )
    templates_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir)
    )

    render_pages(root_dir, templates_env, pages_env)   

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