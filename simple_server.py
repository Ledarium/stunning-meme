import socketserver
import http.server
import urllib.request
from html.parser import HTMLParser
from lxml import etree, html
import re

REMOTE_ADDRESS = "https://news.ycombinator.com"
LOCAL_PORT = 8232
LOCAL_ADDRESS = "http://127.0.0.1:" + str(LOCAL_PORT)


def link_repl_func(link):
    link = re.sub(REMOTE_ADDRESS, LOCAL_ADDRESS, link)
    return link


class MyProxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url = self.path[1:]
        with urllib.request.urlopen(f"{REMOTE_ADDRESS}/{url}") as response:
            self.send_response(200)
            headers = response.headers
            self.end_headers()

            print("here")
            if re.match(r"(.css|.js|.gif|.ico)[?$]", url):
                print("match")
                self.copyfile(response, self.wfile)
                return

            response_content = response.read()
            tree = html.fromstring(response_content)
            tree.rewrite_links(
                link_repl_func, resolve_base_href=True, base_href=REMOTE_ADDRESS
            )
            for tag in tree.iter():
                if tag.text:
                    if tag.tag in set(("span", "div", "p", "i", "b")):
                        tag.text = re.sub(
                            r"([\W^]\w{6})([\W$])", r"\g<1>™\g<2>", tag.text
                        )
            element_tree = etree.ElementTree(tree)

            """
            base_tag = etree.ElementTree.Element("base")
            base_tag["href"] = LOCAL_ADDRESS
            element_tree.insert(base_tag)
            """

            element_tree.write("output.html", method="html", pretty_print=True)
            self.copyfile(open("output.html", "rb"), self.wfile)


httpd = socketserver.ForkingTCPServer(("", LOCAL_PORT), MyProxy)
httpd.serve_forever()
# httpd.handle_request()
