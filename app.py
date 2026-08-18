"""
app.py — ResearchRadar Flask application.

Routes
------
GET /                        Home page — featured papers (2-hop: Paper->Topic + Paper->Researcher)
GET /search?q=<term>         Universal search across Researcher, Paper, Topic nodes
GET /researcher/<name>       Researcher profile with:
                               - authored papers
                               - co-authors (2-hop: Researcher→Paper←Researcher)
                               - research topics (2-hop: Researcher→Paper→Topic)
                               - recommended papers (3-hop: Researcher→Paper←Researcher→Paper)
GET /paper/<title>           Paper detail with:
                               - abstract, authors, topics
                               - related papers via shared topic (2-hop: Paper→Topic←Paper)

All user-supplied values are passed as Cypher parameters ($param) — never concatenated.
"""

from flask import Flask, render_template, request, abort
from neo4j.exceptions import ServiceUnavailable, AuthError
from werkzeug.exceptions import HTTPException
from db import db

app = Flask(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _db_error_response(context: str = ""):
    """Render a user-friendly error page instead of a raw 500 traceback."""
    return render_template("error.html", context=context), 503


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """
    Home page — fetch up to 6 featured papers with their authors and topics.

    Cypher pattern (2-hop from Paper):
        MATCH (p:Paper)
        OPTIONAL MATCH (r:Researcher)-[:AUTHORED]->(p)
        OPTIONAL MATCH (p)-[:ABOUT]->(t:Topic)
    """
    session = db.get_session()
    try:
        cypher = """
        MATCH (p:Paper)
        OPTIONAL MATCH (r:Researcher)-[:AUTHORED]->(p)
        OPTIONAL MATCH (p)-[:ABOUT]->(t:Topic)
        RETURN p,
               collect(DISTINCT r.name) AS author_names,
               collect(DISTINCT t.name) AS topic_names
        LIMIT 6
        """
        result = session.run(cypher)
        featured = []
        for record in result:
            paper = dict(record["p"])
            paper["author_names"] = record["author_names"]
            paper["topic_names"]  = record["topic_names"]
            featured.append(paper)
        return render_template("index.html", featured_papers=featured)
    except (ServiceUnavailable, AuthError) as e:
        print(f"[ERROR] DB unavailable on index: {e}")
        return _db_error_response("home page")
    except Exception as e:
        print(f"[ERROR] index: {e}")
        return render_template("index.html", featured_papers=[])
    finally:
        session.close()


@app.route("/search")
def search():
    """
    Universal search — case-insensitive CONTAINS match across all node types.

    Cypher pattern:
        MATCH (n)
        WHERE (n:Researcher AND toLower(n.name) CONTAINS toLower($q))
           OR (n:Paper      AND toLower(n.title) CONTAINS toLower($q))
           OR (n:Topic      AND toLower(n.name) CONTAINS toLower($q))

    $q is a Cypher parameter — never concatenated into the query string.
    """
    query = request.args.get("q", "").strip()
    if not query:
        return render_template("search_results.html", query=query, results=[])

    session = db.get_session()
    try:
        cypher = """
        MATCH (n)
        WHERE (n:Researcher AND toLower(n.name)  CONTAINS toLower($q))
           OR (n:Paper      AND toLower(n.title) CONTAINS toLower($q))
           OR (n:Topic      AND toLower(n.name)  CONTAINS toLower($q))
        RETURN labels(n)[0] AS type, n AS node
        LIMIT 50
        """
        result = session.run(cypher, q=query)
        results = [
            {"type": record["type"], "data": dict(record["node"])}
            for record in result
        ]
        return render_template("search_results.html", query=query, results=results)
    except (ServiceUnavailable, AuthError) as e:
        print(f"[ERROR] DB unavailable on search: {e}")
        return _db_error_response("search")
    except Exception as e:
        print(f"[ERROR] search: {e}")
        return render_template(
            "search_results.html", query=query, results=[],
            error="An error occurred while searching. Please try again."
        )
    finally:
        session.close()


@app.route("/researcher/<name>")
def researcher(name):
    """
    Researcher profile page.

    Query 1 — authored papers and co-authors (2-hop):
        (Researcher)-[:AUTHORED]->(Paper)<-[:AUTHORED]-(co-Researcher)

    Query 2 — research topics (2-hop: Researcher → Paper → Topic):
        (Researcher)-[:AUTHORED]->(Paper)-[:ABOUT]->(Topic)

    Query 3 — recommended papers (3-HOP — graph-native traversal):
        (Researcher)-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(co:Researcher)
                    -[:AUTHORED]->(suggested:Paper)
        WHERE NOT (Researcher)-[:AUTHORED]->(suggested)

    This 3-hop pattern discovers papers authored by collaborators that the
    target researcher has not yet published themselves — a classic graph
    recommendation problem that would require 3 self-joins in a relational DB.

    $name is a Cypher parameter.
    """
    session = db.get_session()
    try:
        # ── Query 1: profile + papers + co-authors (2-hop) ──────────────────
        q1 = """
        MATCH (r:Researcher {name: $name})
        OPTIONAL MATCH (r)-[:AUTHORED]->(p:Paper)
        OPTIONAL MATCH (p)<-[:AUTHORED]-(co:Researcher) WHERE co <> r
        RETURN r,
               collect(DISTINCT p)  AS papers,
               collect(DISTINCT co) AS coauthors
        """
        result = session.run(q1, name=name).single()
        if not result or not result["r"]:
            abort(404)

        researcher_node = dict(result["r"])
        papers    = [dict(p) for p in result["papers"]    if p is not None]
        coauthors = [dict(c) for c in result["coauthors"] if c is not None]

        # ── Query 2: research topics (2-hop) ────────────────────────────────
        q2 = """
        MATCH (r:Researcher {name: $name})-[:AUTHORED]->(p:Paper)-[:ABOUT]->(t:Topic)
        RETURN DISTINCT t.name AS topic
        ORDER BY t.name
        """
        topics_result = session.run(q2, name=name)
        topics = [record["topic"] for record in topics_result]

        # ── Query 3: recommended papers (3-HOP graph traversal) ─────────────
        # Pattern: Researcher → Paper ← co-Researcher → suggested Paper (3 hops)
        # Step 1: collect all paper IDs already authored by this researcher
        # Step 2: walk the 3-hop path; filter out own papers using the collected set
        q3 = """
        MATCH (r:Researcher {name: $name})-[:AUTHORED]->(own:Paper)
        WITH r, collect(own.title) AS own_titles
        MATCH (r)-[:AUTHORED]->(p:Paper)<-[:AUTHORED]-(co:Researcher)-[:AUTHORED]->(suggested:Paper)
        WHERE co <> r
          AND NOT suggested.title IN own_titles
          AND NOT suggested.title = p.title
        WITH suggested, collect(DISTINCT co.name) AS via_authors, count(DISTINCT co) AS strength
        ORDER BY strength DESC
        RETURN suggested, via_authors
        LIMIT 4
        """
        rec_result  = session.run(q3, name=name)
        recommended = []
        for record in rec_result:
            item = dict(record["suggested"])
            item["via_authors"] = record["via_authors"]
            recommended.append(item)

        return render_template(
            "researcher.html",
            researcher=researcher_node,
            papers=papers,
            coauthors=coauthors,
            topics=topics,
            recommended=recommended,
        )
    except HTTPException:
        raise
    except (ServiceUnavailable, AuthError) as e:
        print(f"[ERROR] DB unavailable on researcher/{name}: {e}")
        return _db_error_response("researcher profile")
    except Exception as e:
        print(f"[ERROR] researcher/{name}: {e}")
        return _db_error_response("researcher profile")
    finally:
        session.close()


@app.route("/paper/<title>")
def paper(title):
    """
    Paper detail page.

    Query 1 — paper, authors, topics:
        MATCH (p:Paper {title: $title})
        OPTIONAL MATCH (r:Researcher)-[:AUTHORED]->(p)
        OPTIONAL MATCH (p)-[:ABOUT]->(t:Topic)

    Query 2 — related papers via shared topic (2-hop graph traversal):
        (Paper)-[:ABOUT]->(Topic)<-[:ABOUT]-(related:Paper)

    This pattern finds papers that share at least one research topic with the
    current paper. In a relational DB this requires joining papers → paper_topics
    → paper_topics → papers — a query that degrades as topics and papers grow.
    Here it is a single 2-hop Cypher traversal, naturally expressed in the graph.

    $title is a Cypher parameter.
    """
    session = db.get_session()
    try:
        # ── Query 1: paper detail ────────────────────────────────────────────
        q1 = """
        MATCH (p:Paper {title: $title})
        OPTIONAL MATCH (r:Researcher)-[auth:AUTHORED]->(p)
        OPTIONAL MATCH (p)-[rel:ABOUT]->(t:Topic)
        RETURN p,
               collect(DISTINCT {researcher: r, order: auth.order}) AS author_rels,
               collect(DISTINCT {topic: t, relevance: rel.relevance}) AS topic_rels
        """
        result = session.run(q1, title=title).single()
        if not result or not result["p"]:
            abort(404)

        paper_node = dict(result["p"])

        # Sort authors by contribution order
        author_rels = sorted(
            [rec for rec in result["author_rels"] if rec["researcher"] is not None],
            key=lambda x: x["order"] if x["order"] is not None else 99
        )
        authors = [dict(rec["researcher"]) for rec in author_rels]

        # Separate primary and secondary topics
        topic_rels = [rec for rec in result["topic_rels"] if rec["topic"] is not None]
        topics = [dict(rec["topic"]) for rec in topic_rels]
        primary_topics   = [dict(rec["topic"]) for rec in topic_rels if rec["relevance"] == "primary"]
        secondary_topics = [dict(rec["topic"]) for rec in topic_rels if rec["relevance"] == "secondary"]

        # ── Query 2: related papers via shared topic (2-hop) ─────────────────
        q2 = """
        MATCH (p:Paper {title: $title})-[:ABOUT]->(t:Topic)<-[:ABOUT]-(related:Paper)
        WHERE related <> p
        WITH related, collect(DISTINCT t.name) AS shared_topics, count(DISTINCT t) AS overlap
        ORDER BY overlap DESC
        RETURN related, shared_topics
        LIMIT 4
        """
        rel_result = session.run(q2, title=title)
        related_papers = []
        for record in rel_result:
            item = dict(record["related"])
            item["shared_topics"] = record["shared_topics"]
            related_papers.append(item)

        return render_template(
            "paper.html",
            paper=paper_node,
            authors=authors,
            topics=topics,
            primary_topics=primary_topics,
            secondary_topics=secondary_topics,
            related_papers=related_papers,
        )
    except HTTPException:
        raise
    except (ServiceUnavailable, AuthError) as e:
        print(f"[ERROR] DB unavailable on paper/{title}: {e}")
        return _db_error_response("paper detail")
    except Exception as e:
        print(f"[ERROR] paper/{title}: {e}")
        return _db_error_response("paper detail")
    finally:
        session.close()


# ── Error handlers ────────────────────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(503)
def service_unavailable(e):
    return render_template("error.html", context=""), 503


if __name__ == "__main__":
    app.run(debug=True)
