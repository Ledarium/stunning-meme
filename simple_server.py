import socketserver
import http.server
import urllib.request
from html.parser import HTMLParser
from lxml import etree, html
import re
import os

REMOTE_ADDRESS = "https://news.ycombinator.com"
LOCAL_PORT = 8232
LOCAL_ADDRESS = "http://127.0.0.1:" + str(LOCAL_PORT)
TMP_FILENAME = "tmp_output"


class MyProxy(http.server.SimpleHTTPRequestHandler):
    """
    Class to serve remote pages, adding ™ after every 6-letter word.
    """

    def do_GET(self):
        """
        Do GET request and if it is plain html, process its content.
        """
        url = self.path[1:]
        with urllib.request.urlopen(f"{REMOTE_ADDRESS}/{url}") as response:
            self.send_response(200)
            self.end_headers()

            if re.search(r"(.css|.gif|.ico)($|\?)", url):
                self.copyfile(response, self.wfile)
                return

            response_content = response.read()
            hp = etree.HTMLParser(encoding="utf-8")
            tree = html.fromstring(response_content, parser=hp)
            for tag in tree.iter():
                if tag.text and tag.tag in set(("span", "div", "p", "i", "b")):
                    tag.text = re.sub(
                        # pretty self-explanatory
                        r"(\W|^)(\w{6})(\s|(\W\W)|$)",
                        r"\g<1>\g<2>™\g<3>",
                        tag.text,
                    )
            element_tree = etree.ElementTree(tree)
            element_tree.write(TMP_FILENAME, method="html", pretty_print=True)
            self.copyfile(open(TMP_FILENAME, "rb"), self.wfile)


httpd = socketserver.ForkingTCPServer(("", LOCAL_PORT), MyProxy)
try:
    httpd.serve_forever()
except Exception:
    httpd.shutdown()
    os.remove(TMP_FILENAME)

# httpd.handle_request()
