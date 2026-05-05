"""Schema.org sitemap abstractions and implementations."""

from .mycore_solr import MycoreSolrSitemap
from .sitemap import Sitemap
from .xml import XmlSitemap

__all__ = ["Sitemap", "XmlSitemap", "MycoreSolrSitemap"]
