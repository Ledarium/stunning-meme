import socketserver
import http.server
import urllib.request
import urllib.error
from html.parser import HTMLParser
from lxml import etree, html
import re
import pathlib

REMOTE_ADDRESS = "https://news.ycombinator.com"
LOCAL_PORT = 8232
LOCAL_ADDRESS = "http://127.0.0.1:" + str(LOCAL_PORT)
TMP_FILE = pathlib.Path("tmp_output")


def tmify(string):
    """
    Function to add ™ after every 6-letter word
    :param string: String to modify
    :return: Modified string
    """
    return re.sub(
        # pretty self-explanatory
        r"(\W|^)(\w{6})(\s|$|[^a-zA-Z0-9_™](\W|$))",
        r"\1\2™\3",
        string,
    )


class MyProxy(http.server.SimpleHTTPRequestHandler):
    """
    Class to serve remote pages, adding ™ after every 6-letter word.
    """

    def do_GET(self):
        """
        Do GET request and if it is plain html, process its content.
        """
        url = self.path[1:]
        try:
            with urllib.request.urlopen(f"{REMOTE_ADDRESS}/{url}") as response:
                self.send_response(200)
                self.send_header(
                    "Content-Type", response.headers["Content-Type"]
                )
                self.end_headers()

                # it is probably better to check content-type header,
                # but regexeps are fun
                if re.search(r"(.css|.gif|.ico|.js)($|\?)", url):
                    self.copyfile(response, self.wfile)
                    return

                charset = response.info().get_content_charset()
                response_content = response.read().decode(charset)
                hp = etree.HTMLParser()

                tree = html.fromstring(response_content, parser=hp)
                for tag in tree.iter():
                    if tag.tag in set(("span", "div", "p", "i", "b", "a")):
                        if tag.text:
                            tag.text = tmify(tag.text)
                        if tag.tail:
                            tag.tail = tmify(tag.tail)
                        if href := tag.get("href"):
                            tag.attrib["href"] = re.sub(
                                REMOTE_ADDRESS, LOCAL_ADDRESS, href
                            )
                element_tree = etree.ElementTree(tree)
                element_tree.write(
                    str(TMP_FILE), method="html", pretty_print=True
                )
                self.copyfile(open(TMP_FILE, "rb"), self.wfile)
        except urllib.error.HTTPError as exc:
            self.send_response(exc.code)
            self.end_headers()
            self.wfile.write(exc.fp.read())


if __name__ == "__main__":
    httpd = socketserver.ForkingTCPServer(("", LOCAL_PORT), MyProxy)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        TMP_FILE.unlink(missing_ok=True)
