"""Linked Data sitemap abstractions and implementations."""

from middleware.linked_data.sitemap.mycore_solr import MycoreSolrSitemap
from middleware.linked_data.sitemap.regal_find import RegalFindSitemap
from middleware.linked_data.sitemap.sitemap import Sitemap
from middleware.linked_data.sitemap.xml import XmlSitemap

__all__ = ["Sitemap", "XmlSitemap", "MycoreSolrSitemap", "RegalFindSitemap"]
