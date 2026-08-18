# ResearchRadar

> A research knowledge graph application that lets you discover relationships between academic papers, researchers, topics, and institutions — powered by CognoDB (hosted Neo4j) and openCypher graph traversals.

---

## Problem Statement

Academic literature is highly interconnected. A paper builds on prior work, its authors collaborate across institutions, and its topics overlap with adjacent fields. Traditional relational databases model this as flat tables joined by foreign keys — a structure that becomes unwieldy when you need to answer questions like:

- *"Which papers are 2 hops away from this researcher through their collaborators?"*
- *"What other research is connected to this paper through shared topics?"*
- *"Which researchers form clusters around the same set of topics?"*

These are naturally **graph problems**. ResearchRadar models the research landscape as a property graph and uses openCypher traversals to answer these questions directly.

---

## Why a Graph Database?

| Question | Relational DB | Graph DB |
|---|---|---|
| Find a researcher's co-authors | `JOIN papers ON author_id … SELF JOIN` | `(r)-[:AUTHORED]->(p)<-[:AUTHORED]-(co)` |
| Papers sharing a topic with this paper | 3-table JOIN chain | `(p)-[:ABOUT]->(t)<-[:ABOUT]-(related)` |
| Papers by my collaborators I haven't read | 3-level self-join with `NOT IN` | 3-hop Cypher path, one query |
| "Follow the research chain" traversal | Recursive CTEs, O(n²) joins | Variable-length `[:AUTHORED*1..n]` path |

Graph databases represent connections as first-class citizens. Traversal depth is nearly constant regardless of dataset size — unlike relational joins, which grow with the number of rows. CognoDB provides a hosted Neo4j-compatible graph database accessible via the Bolt protocol.

---

## Graph Data Model

```
(:Researcher)──[:AUTHORED {order: int}]──►(:Paper)──[:ABOUT {relevance: str}]──►(:Topic)

Node labels and properties
──────────────────────────
(:Researcher)
  name         String   "Dr. Alice Smith"
  affiliation  String   "Tech University"

(:Paper)
  title        String   "Advances in Deep Learning"
  year         Integer  2023
  abstract     String   "A comprehensive review of..."

(:Topic)
  name         String   "Machine Learning"

Relationship types and properties
──────────────────────────────────
[:AUTHORED]
  order        Integer  1 = first author, 2 = second, ...

[:ABOUT]
  relevance    String   "primary" | "secondary"
```

**Example traversal paths in the seed data:**

```
Dr. Alice Smith ──AUTHORED──► Advances in Deep Learning ──ABOUT──► Machine Learning
                                                           ──ABOUT──► Artificial Intelligence
Dr. Charlie Davis ──AUTHORED──► Advances in Deep Learning    (co-authored, same paper)

3-hop path:
Alice ──AUTHORED──► Neural Networks for Cyber Defense
                    ◄──AUTHORED── Elena Zhao
                                  ──AUTHORED──► Transformer Models for Clinical NLP
```

---

## Seed Dataset

| Category | Count |
|---|---|
| Researchers | 12 |
| Papers | 14 |
| Topics | 10 |
| Institutions | 5 |

**Institutions:** Tech University · MIT · Stanford University · Cambridge University · ETH Zurich · Quantum Institute

**Topics:** Artificial Intelligence · Machine Learning · Quantum Computing · Cybersecurity · Bioinformatics · Data Science · Natural Language Processing · Computer Vision · Distributed Systems · Human-Computer Interaction

---

## Main Cypher Queries

### 1. Universal Search
```cypher
MATCH (n)
WHERE (n:Researcher AND toLower(n.name)  CONTAINS toLower($q))
   OR (n:Paper      AND toLower(n.title) CONTAINS toLower($q))
   OR (n:Topic      AND toLower(n.name)  CONTAINS toLower($q))
RETURN labels(n)[0] AS type, n AS node
LIMIT 50
```
`$q` is always a Cypher parameter — never string-concatenated.

---

### 2. Researcher Profile with Co-authors (2-hop)
```cypher
MATCH (r:Researcher {name: $name})
OPTIONAL MATCH (r)-[:AUTHORED]->(p:Paper)
OPTIONAL MATCH (p)<-[:AUTHORED]-(co:Researcher) WHERE co <> r
RETURN r,
       collect(DISTINCT p)  AS papers,
       collect(DISTINCT co) AS coauthors
```
**Pattern:** `Researcher → Paper ← Researcher` (2 hops)  
**Graph advantage:** Co-author discovery requires only following edges — no self-join.

---

### 3. Research Topics from Authored Papers (2-hop)
```cypher
MATCH (r:Researcher {name: $name})-[:AUTHORED]->(p:Paper)-[:ABOUT]->(t:Topic)
RETURN DISTINCT t.name AS topic
ORDER BY t.name
```
**Pattern:** `Researcher → Paper → Topic` (2 hops)  
Surfaces all research areas a researcher has published in.

---

### 4. Recommended Papers via Collaborator Network (3-HOP — graph-native)
```cypher
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
```
**Pattern:** `Researcher → Paper ← Researcher → Paper` (3 hops)  
**Why graph-native:** This "friend-of-friend paper recommendation" would require 3 self-joins and a `NOT IN` subquery in SQL. In Cypher it is a single, readable path pattern.  
**Used on:** Researcher profile page → "Recommended Reading" section.

---

### 5. Related Papers via Shared Topic (2-hop — graph-native)
```cypher
MATCH (p:Paper {title: $title})-[:ABOUT]->(t:Topic)<-[:ABOUT]-(related:Paper)
WHERE related <> p
WITH related, collect(DISTINCT t.name) AS shared_topics, count(DISTINCT t) AS overlap
ORDER BY overlap DESC
RETURN related, shared_topics
LIMIT 4
```
**Pattern:** `Paper → Topic ← Paper` (2 hops through a shared topic node)  
**Why graph-native:** In a relational DB, finding papers connected through shared topics requires a 3-table join chain (papers → paper_topics → paper_topics → papers) that degrades quadratically. In the graph this is a single 2-hop traversal that scales with the local neighbourhood, not the full dataset.  
**Used on:** Paper detail page → "Related Papers" section.

---

## CognoDB Setup

CognoDB provides a hosted, Neo4j-compatible graph database with a free tier.

1. **Create an account** at [cognodb.com](https://cognodb.com) and sign in.
2. **Create a new database instance** — select the free `c0` tier.
3. **Copy your connection details:**
   - URI: `bolt+s://<your-instance>.databases.cognodb.com`
   - Username: `cognodb` (default)
   - Password: shown once at creation — copy it immediately.
4. **Create a `.env` file** in the project root (never commit this file):
   ```env
   COGNODB_URI=bolt+s://<your-instance>.databases.cognodb.com
   COGNODB_USERNAME=cognodb
   COGNODB_PASSWORD=<your-password>
   ```
5. Confirm `.env` is listed in `.gitignore` before your first commit.

---

## Local Setup

### Prerequisites
- Python 3.9+
- Git

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd researchradar
```

### 2. Create a virtual environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Create `.env` in the project root with your CognoDB credentials (see CognoDB Setup above).

### 5. Seed the database
```bash
python seed.py
```
This clears the existing graph and inserts 12 researchers, 14 papers, and 10 topics.

### 6. Run the application
```bash
flask run
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## Environment Variables

| Variable | Description |
|---|---|
| `COGNODB_URI` | Bolt URI for your CognoDB instance (`bolt+s://...`) |
| `COGNODB_USERNAME` | CognoDB username (default: `cognodb`) |
| `COGNODB_PASSWORD` | CognoDB password — **never commit this** |

---

## Project Structure

```
researchradar/
├── app.py              # Flask routes and Cypher queries
├── db.py               # CognoDB connection via Neo4j Python driver
├── seed.py             # Graph seed script (researchers, papers, topics)
├── requirements.txt    # Python dependencies
├── .env                # Credentials — NOT committed (in .gitignore)
├── .gitignore
├── templates/
│   ├── base.html       # Shared layout and navigation
│   ├── index.html      # Home page with featured papers
│   ├── search_results.html
│   ├── paper.html      # Paper detail with related papers (2-hop)
│   ├── researcher.html # Researcher profile with recommendations (3-hop)
│   ├── 404.html
│   └── error.html      # DB connection error page
└── static/
    ├── css/style.css   # Design system
    └── js/main.js
```

---

## Screenshots

> Run the application locally (`flask run`) and navigate to `http://127.0.0.1:5000` to see the live UI.

Key pages to explore:
- **Home** — featured papers grid with topic pills and author names
- **Search** — try `"Machine Learning"`, `"Alice"`, or `"Quantum"`
- **Paper detail** — abstract, primary/secondary topics, related papers via 2-hop traversal
- **Researcher profile** — authored papers, co-authors, research topics, and 3-hop recommended reading

---

## Hosted Demo

> *(Add your deployment URL here if hosting on Render, Railway, or Fly.io)*

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `flask` | 3.0.3 | Web framework |
| `neo4j` | 5.23.1 | Official Neo4j Python driver (Bolt protocol) |
| `python-dotenv` | 1.0.1 | Load `.env` credentials at runtime |
