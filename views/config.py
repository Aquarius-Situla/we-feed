import os
from core.config import cfg
class Config:
    base_path= "./public"
    #模板路径 
    public_dir = f"{base_path}/templates/"
    home_template = f"{base_path}/templates/home.html"
    mps_template = f"{base_path}/templates/mps.html"
    tags_template = f"{base_path}/templates/tags.html"
    tags_articles_template = f"{base_path}/templates/tags_articles.html"
    article_template = f"{base_path}/templates/article.html"
    article_detail_template = f"{base_path}/templates/article_detail.html"
    article_detail_print_template = f"{base_path}/templates/print.html"
    articles_template = f"{base_path}/templates/articles.html"
    site={
        "name": cfg.get("site.name", "WeFeed"),
        "description": cfg.get("site.description", "A WeChat Official Account RSS Reader"), 
        "keywords": cfg.get("site.keywords", "WeFeed,WeRss,RSS,微信公众号,RSS订阅,RSS阅读器,RSS订阅助手"),
        "logo": cfg.get("site.logo", "/static/logo.svg"),
        "favicon": cfg.get("site.favicon", "/static/logo.svg"),
        "author": cfg.get("site.author", "Situla"),
        "copyright": cfg.get("site.copyright", "© 2026 Situla · WeFeed"),
    }
base = Config()