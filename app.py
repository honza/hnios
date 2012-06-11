import os
from flask import Flask
import requests
from pyquery import PyQuery as pq
import redis


url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
r = redis.from_url(url)

app = Flask(__name__)


def get_html():
    r = requests.get("http://news.ycombinator.com")
    return r.text.encode('utf-8')


def parse_a(a):
    return {
        'href': a.attrib['href'],
        'text': a.text
    }


def parse_html(html):
    d = pq(html)
    return map(parse_a, d('.title a'))


def make_link(a):
    return "<div class='item'><h2><a href='%s'>%s</a></h2></div>" % (a['href'], a['text'])


def render_html(data):
    with open('template.html') as f:
        template = f.read()
    links = "\n".join(map(make_link, data[:(len(data) - 1)]))
    return template % (links)


@app.route("/")
def main():
    html = r.get("html")
    if html:
        return html

    html = get_html()
    parsed = parse_html(html)
    rendered = render_html(parsed)

    # Cache for 15min
    r.set("html", rendered)
    r.expire("html", 60 * 15)
    return rendered


if __name__ == '__main__':
    app.run()
