from .romhustler import RomHustlerScraper
from .vimm import VimmScraper
from .archiveorg import ArchiveOrgScraper

SCRAPERS = [
    RomHustlerScraper(),
    VimmScraper(),
    ArchiveOrgScraper(),
] 