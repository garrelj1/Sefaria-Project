# -*- coding: utf-8 -*-
"""
summaries.py - create and manage Table of Contents document for all texts

Writes to MongoDB Collection: summaries
"""
import json
from datetime import datetime
from pprint import pprint

import sefaria.system.cache as scache
from sefaria.system.database import db
from sefaria.utils.hebrew import hebrew_term
from model import *
from sefaria.system.exceptions import BookNameError
import logging
logger = logging.getLogger(__name__)

# Giant list ordering or categories
# indentation and inclusion of duplicate categories (like "Seder Moed")
# is for readability only. The table of contents will follow this structure.
ORDER = [
    "Tanach",
        "Torah",
            "Genesis",
            "Exodus",
            "Leviticus",
            "Numbers",
            "Deuteronomy",
        "Prophets",
        "Writings",
        "Targum",
            'Onkelos Genesis',
            'Onkelos Exodus',
            'Onkelos Leviticus',
            'Onkelos Numbers',
            'Onkelos Deuteronomy',
            'Targum Jonathan on Genesis',
            'Targum Jonathan on Exodus',
            'Targum Jonathan on Leviticus',
            'Targum Jonathan on Numbers',
            'Targum Jonathan on Deuteronomy',
    "Mishnah",
        "Seder Zeraim",
        "Seder Moed",
        "Seder Nashim",
        "Seder Nezikin",
        "Seder Kodashim",
        "Seder Tahorot",
    "Tosefta",
        "Seder Zeraim",
        "Seder Moed",
        "Seder Nashim",
        "Seder Nezikin",
        "Seder Kodashim",
        "Seder Tahorot",
    "Talmud",
        "Bavli",
                "Seder Zeraim",
                "Seder Moed",
                "Seder Nashim",
                "Seder Nezikin",
                "Seder Kodashim",
                "Seder Tahorot",
        "Yerushalmi",
                "Seder Zeraim",
                "Seder Moed",
                "Seder Nashim",
                "Seder Nezikin",
                "Seder Kodashim",
                "Seder Tahorot",
        "Rif",
    "Midrash",
        "Aggadic Midrash",
            "Midrash Rabbah",
        "Halachic Midrash",
    "Halakhah",
        "Mishneh Torah",
            'Introduction',
            'Sefer Madda',
            'Sefer Ahavah',
            'Sefer Zemanim',
            'Sefer Nashim',
            'Sefer Kedushah',
            'Sefer Haflaah',
            'Sefer Zeraim',
            'Sefer Avodah',
            'Sefer Korbanot',
            'Sefer Taharah',
            'Sefer Nezikim',
            'Sefer Kinyan',
            'Sefer Mishpatim',
            'Sefer Shoftim',
        "Shulchan Arukh",
    "Kabbalah",
        "Zohar",
    'Liturgy',
        'Siddur',
        'Piyutim',
    'Philosophy',
    'Parshanut',
    'Chasidut',
    'Musar',
    'Responsa',
        "Rashba",
        "Rambam",
    'Apocrypha',
    'Elucidation',
    'Modern Works',
    'Other',
]

REORDER_RULES = {
    "Commentary2": ["Commentary"],
}

#//todo: mark for commentary refactor
def update_table_of_contents():
    toc = []
    sparseness_dict = get_sparesness_lookup()
    # Add an entry for every text we know about
    indices = IndexSet()
    for i in indices:
        if i.is_commentary() or i.categories[0] == "Commentary2":
            # Special case commentary below
            continue

        if i.categories[0] in REORDER_RULES:
            cats = REORDER_RULES[i.categories[0]] + i.categories[1:]
        else:
            cats = i.categories[:]
        if cats[0] not in ORDER:
            cats.insert(0, "Other")

        node = get_or_make_summary_node(toc, cats)
        text = i.toc_contents()
        text["sparseness"] = sparseness_dict[text["title"]]
        node.append(text)

    # Special handling to list available commentary texts
    commentary_texts = library.get_commentary_version_titles(with_commentary2=True)
    for c in commentary_texts:

        try:
            i = library.get_index(c)
        except BookNameError:
            continue

        if i.categories[0] in REORDER_RULES:
            cats = REORDER_RULES[i.categories[0]] + i.categories[1:]
        else:
            cats = i.categories[:]

        text = i.toc_contents()
        text["sparseness"] = sparseness_dict[text["title"]]

        cats[0], cats[1] = cats[1], cats[0] # Swap "Commentary" with toplevel category (e.g., "Tanach")
        node = get_or_make_summary_node(toc, cats)
        node.append(text)

    # Recursively sort categories and texts
    return sort_toc_node(toc, recur=True)

def recur_delete_element_from_toc(bookname, toc):
    for toc_elem in toc:
        #base element, a text- check if title matches.
        if 'title' in toc_elem:
            if toc_elem['title'] == bookname:
                #if there is a match, append to this recursion's list of results.
                toc_elem['to_delete'] = True
        #category
        elif 'category' in toc_elem:
            #first go down the tree
            toc_elem['contents'][:] = [x for x in recur_delete_element_from_toc(bookname, toc_elem['contents']) if not 'to_delete' in x]
            #add the current category name to any already-found results (since at this point we are on our way up from the recursion.
            if not len(toc_elem['contents']):
                toc_elem['to_delete'] = True
    return toc

#//todo: mark for commentary refactor
def update_title_in_toc(toc, index, old_ref=None, recount=True):
    """
    Update text summary docs to account for change or insertion of 'text'
    * recount - whether or not to perform a new count of available text
    """
    indx_dict = index.toc_contents()

    if recount:
        VersionState(index.title).refresh()
    resort_other = False

    if indx_dict["categories"][0] in REORDER_RULES:
        indx_dict["categories"] = REORDER_RULES[indx_dict["categories"][0]] + indx_dict["categories"][1:]

    if indx_dict["categories"][0] != "Commentary":
        if indx_dict["categories"][0] not in ORDER:
            indx_dict["categories"].insert(0, "Other")
            resort_other = True
        node = get_or_make_summary_node(toc, indx_dict["categories"])
        text = add_counts_to_index(indx_dict)
    else:
        commentator = indx_dict["commentator"]
        cats = [indx_dict["categories"][1], "Commentary", commentator]
        node = get_or_make_summary_node(toc, cats)
        text = add_counts_to_index(indx_dict)

    found = False
    test_title = old_ref or text["title"]
    for item in node:
        if item.get("title") == test_title:
            item.update(text)
            found = True
            break
    if not found:
        node.append(text)
        node[:] = sort_toc_node(node)

    # If a new category may have been added to other, resort the categories
    if resort_other:
        toc[-1]["contents"] = sort_toc_node(toc[-1]["contents"])

    return toc


def get_or_make_summary_node(summary, nodes, contents_only=True, make_if_not_found=True):
    """
    Returns the node in 'summary' that is named by the list of categories in 'nodes',
    If make_if_not_found is true, creates the node if it doesn't exist.
    Used recursively on sub-summaries.
    """
    if len(nodes) == 1:
    # Basecase, only need to search through one level
        for node in summary:
            if node.get("category") == nodes[0]:
                return node["contents"] if contents_only else node
        # we didn't find it, so let's add it
        if make_if_not_found:
            summary.append({"category": nodes[0], "heCategory": hebrew_term(nodes[0]), "contents": []})
            return summary[-1]["contents"] if contents_only else summary[-1]
        else:
            return None

    # Look for the first category, or add it, then recur
    for node in summary:
        if node.get("category") == nodes[0]:
            return get_or_make_summary_node(node["contents"], nodes[1:], contents_only=contents_only)

    if make_if_not_found:
        summary.append({"category": nodes[0], "heCategory": hebrew_term(nodes[0]), "contents": []})
        return get_or_make_summary_node(summary[-1]["contents"], nodes[1:], contents_only=contents_only)
    else:
        return None


def get_sparesness_lookup():
    vss = db.vstate.find({}, {"title": 1, "content._en.sparseness": 1, "content._he.sparseness": 1})
    return {vs["title"]: max(vs["content"]["_en"]["sparseness"], vs["content"]["_he"]["sparseness"]) for vs in vss}


def add_counts_to_index(indx_dict):
    """
    Returns a dictionary which decorates `indx_dict` with a spareness score.
    """
    vs = StateNode(indx_dict["title"], meta=True)
    indx_dict["sparseness"] = max(vs.get_sparseness("he"), vs.get_sparseness("en"))
    return indx_dict


def node_sort_key(a):
    """
    Sort function for texts/categories per below.
    """
    if "category" in a:
        try:
            return ORDER.index(a["category"])
        except ValueError:
           return 'zz' + a["category"]
    elif "title" in a:
        try:
            return ORDER.index(a["title"])
        except ValueError:
            if "order" in a:
                return a["order"][0]
            else:
                return a["title"]

    return None


def node_sort_sparse(a):
    if "category" in a or "order" in a:
        # Keep categories or texts with explicit orders at top
        score = -4
    else:
        score = -a.get('sparseness', 1)

    return score


def sort_toc_node(node, recur=False):
    """
    Sort the texts and categories in node according to:
    1. the order of categories and texts listed in the global var 'order'
    2. the order field on a text
    3. alphabetically

    If 'recur', call sort_toc_node on each category in 'node' as well.
    """
    node = sorted(node, key=node_sort_key)
    node = sorted(node, key=node_sort_sparse)

    if recur:
        for cat in node:
            if "category" in cat:
                cat["contents"] = sort_toc_node(cat["contents"], recur=True)

    return node


def get_texts_summaries_for_category(category):
    """
    Returns the list of texts records in the table of contents corresponding to "category".
    """
    toc = library.get_toc()
    matched_category = find_category_node(category, toc)
    if matched_category:
        return extract_text_records_from_toc(matched_category["contents"])


def find_category_node(category, toc):
    matched_category_elem = None
    for elem in toc:
        if "category" in elem:
            if elem["category"] == category:
                matched_category_elem = elem
                break
            else:
                matched_category_elem = find_category_node(category, elem["contents"])
                if matched_category_elem:
                    break
    return matched_category_elem


def extract_text_records_from_toc(toc):
    summary = []
    for elem in toc:
        if "category" in elem:
            summary += extract_text_records_from_toc(elem["contents"])
        else:
            summary += [elem]
    return summary


def flatten_toc(toc, include_categories=False, categories_in_titles=False, version_granularity=False):
    """
    Returns an array of strings which corresponds to each category and text in the
    Table of Contents in order.

    - categories_in_titles: whether to include each category preceding a text title,
        e.g., "Tanach > Torah > Genesis".
    - version_granularity: whether to include a separate entry for every text version.
    """
    results = []
    for x in toc:
        name = x.get("category", None) or x.get("title", None)
        if "category" in x:
            if include_categories:
                results += [name]
            subcats = flatten_toc(x["contents"], categories_in_titles=categories_in_titles)
            if categories_in_titles:
                subcats = ["%s > %s" %(name, y) for y in subcats]
            results += subcats

        elif "title" in x:
            if not version_granularity:
                results += [name]
            else:
                #versions = texts.get_version_list(name)
                versions = Ref(name).version_list()
                for v in versions:
                    lang = {"he": "Hebrew", "en": "English"}[v["language"]]
                    results += ["%s > %s > %s.json" % (name, lang, v["versionTitle"])]

    return results

