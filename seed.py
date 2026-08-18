"""
seed.py — ResearchRadar database seeding script.

Clears the existing graph and populates it with a realistic research knowledge graph
containing 12 researchers across 5 institutions, 14 papers, and 10 topic areas.

Relationship properties:
  [:AUTHORED {order: int}]      — author contribution order (1 = first author)
  [:ABOUT {relevance: str}]     — "primary" or "secondary" topic classification
"""

from db import db

# ── Data ──────────────────────────────────────────────────────────────────────

TOPICS = [
    "Artificial Intelligence",
    "Machine Learning",
    "Quantum Computing",
    "Cybersecurity",
    "Bioinformatics",
    "Data Science",
    "Natural Language Processing",
    "Computer Vision",
    "Distributed Systems",
    "Human-Computer Interaction",
]

RESEARCHERS = [
    {"name": "Dr. Alice Smith",       "affiliation": "Tech University"},
    {"name": "Prof. Bob Jones",        "affiliation": "Quantum Institute"},
    {"name": "Dr. Charlie Davis",      "affiliation": "Tech University"},
    {"name": "Dr. Elena Zhao",         "affiliation": "MIT"},
    {"name": "Prof. Raj Patel",        "affiliation": "Stanford University"},
    {"name": "Dr. Sarah Kim",          "affiliation": "Cambridge University"},
    {"name": "Prof. Marcus Weber",     "affiliation": "ETH Zurich"},
    {"name": "Dr. Fatima Al-Rashid",   "affiliation": "MIT"},
    {"name": "Prof. James O'Brien",    "affiliation": "Stanford University"},
    {"name": "Dr. Priya Nair",         "affiliation": "Tech University"},
    {"name": "Dr. Lena Fischer",       "affiliation": "ETH Zurich"},
    {"name": "Prof. Omar Hassan",      "affiliation": "Cambridge University"},
]

PAPERS = [
    {
        "title": "Advances in Deep Learning",
        "year": 2023,
        "abstract": (
            "A comprehensive review of modern deep learning architectures—transformers, "
            "diffusion models, and mixture-of-experts—and their applications across vision, "
            "language, and multimodal tasks. We survey training efficiency techniques and "
            "emerging scaling laws."
        ),
        "authors": [
            {"name": "Dr. Alice Smith",  "order": 1},
            {"name": "Dr. Charlie Davis","order": 2},
        ],
        "topics": [
            {"name": "Artificial Intelligence", "relevance": "primary"},
            {"name": "Machine Learning",         "relevance": "primary"},
        ],
    },
    {
        "title": "Neural Networks for Cyber Defense",
        "year": 2022,
        "abstract": (
            "Applying deep neural networks to intrusion detection, malware classification, "
            "and real-time threat analysis in enterprise environments. We evaluate CNN, LSTM, "
            "and graph neural network approaches on the CICIDS and UNSW-NB15 benchmark datasets."
        ),
        "authors": [
            {"name": "Dr. Alice Smith", "order": 1},
            {"name": "Dr. Elena Zhao",  "order": 2},
        ],
        "topics": [
            {"name": "Cybersecurity",           "relevance": "primary"},
            {"name": "Artificial Intelligence", "relevance": "secondary"},
            {"name": "Machine Learning",        "relevance": "secondary"},
        ],
    },
    {
        "title": "Quantum Error Correction at Scale",
        "year": 2023,
        "abstract": (
            "Novel stabilizer codes and fault-tolerant protocols for suppressing decoherence "
            "in superconducting qubit arrays. We demonstrate performance beyond the surface "
            "code threshold on a 72-qubit processor and propose a path to logical error rates "
            "below 10^-6."
        ),
        "authors": [
            {"name": "Prof. Bob Jones",    "order": 1},
            {"name": "Prof. Marcus Weber", "order": 2},
        ],
        "topics": [
            {"name": "Quantum Computing", "relevance": "primary"},
        ],
    },
    {
        "title": "Data Privacy in Healthcare",
        "year": 2021,
        "abstract": (
            "A framework combining differential privacy and secure multi-party computation "
            "for electronic health records. We show that privacy-preserving analytics can be "
            "achieved with less than 3% utility loss across three real-world hospital datasets."
        ),
        "authors": [
            {"name": "Dr. Charlie Davis", "order": 1},
            {"name": "Dr. Priya Nair",    "order": 2},
        ],
        "topics": [
            {"name": "Bioinformatics", "relevance": "primary"},
            {"name": "Data Science",   "relevance": "secondary"},
            {"name": "Cybersecurity",  "relevance": "secondary"},
        ],
    },
    {
        "title": "Transformer Models for Clinical NLP",
        "year": 2023,
        "abstract": (
            "Fine-tuning large language models on de-identified clinical notes to extract "
            "structured diagnoses, medications, and adverse events. Our clinical BERT variant "
            "achieves state-of-the-art F1 on i2b2 and MedNLI benchmarks."
        ),
        "authors": [
            {"name": "Dr. Elena Zhao",       "order": 1},
            {"name": "Dr. Fatima Al-Rashid", "order": 2},
        ],
        "topics": [
            {"name": "Natural Language Processing", "relevance": "primary"},
            {"name": "Machine Learning",             "relevance": "secondary"},
            {"name": "Bioinformatics",               "relevance": "secondary"},
        ],
    },
    {
        "title": "Federated Learning for Privacy-Preserving Analytics",
        "year": 2022,
        "abstract": (
            "A federated learning framework that trains shared models across decentralized "
            "data silos with formal differential privacy guarantees. We provide convergence "
            "proofs under non-IID data distributions and demonstrate a 40% reduction in "
            "communication cost over baseline FedAvg."
        ),
        "authors": [
            {"name": "Dr. Fatima Al-Rashid", "order": 1},
            {"name": "Prof. Raj Patel",       "order": 2},
        ],
        "topics": [
            {"name": "Machine Learning", "relevance": "primary"},
            {"name": "Data Science",     "relevance": "secondary"},
            {"name": "Cybersecurity",    "relevance": "secondary"},
        ],
    },
    {
        "title": "Computer Vision in Medical Imaging",
        "year": 2022,
        "abstract": (
            "Vision transformer and CNN architectures for automated tumour segmentation, "
            "retinal disease detection, and digital pathology slide analysis. Our models "
            "achieve radiologist-level accuracy on five public benchmarks."
        ),
        "authors": [
            {"name": "Dr. Sarah Kim",  "order": 1},
            {"name": "Dr. Priya Nair", "order": 2},
        ],
        "topics": [
            {"name": "Computer Vision",  "relevance": "primary"},
            {"name": "Bioinformatics",   "relevance": "secondary"},
            {"name": "Machine Learning", "relevance": "secondary"},
        ],
    },
    {
        "title": "Quantum Machine Learning Algorithms",
        "year": 2023,
        "abstract": (
            "Variational quantum circuits and quantum kernel methods for supervised "
            "classification on near-term NISQ hardware. We provide empirical benchmarks "
            "on six datasets and discuss the conditions under which quantum advantage "
            "is achievable."
        ),
        "authors": [
            {"name": "Prof. Bob Jones", "order": 1},
            {"name": "Prof. Raj Patel", "order": 2},
        ],
        "topics": [
            {"name": "Quantum Computing", "relevance": "primary"},
            {"name": "Machine Learning",  "relevance": "secondary"},
        ],
    },
    {
        "title": "Adversarial Robustness in Neural Networks",
        "year": 2022,
        "abstract": (
            "Certified defenses against L-infinity adversarial perturbations using "
            "randomized smoothing, interval bound propagation, and Lipschitz-constrained "
            "architectures. We establish new certified accuracy records on CIFAR-10 and "
            "ImageNet under standard threat models."
        ),
        "authors": [
            {"name": "Dr. Alice Smith",    "order": 1},
            {"name": "Prof. James O'Brien","order": 2},
        ],
        "topics": [
            {"name": "Cybersecurity",   "relevance": "primary"},
            {"name": "Machine Learning","relevance": "secondary"},
            {"name": "Computer Vision", "relevance": "secondary"},
        ],
    },
    {
        "title": "Distributed Graph Processing at Scale",
        "year": 2021,
        "abstract": (
            "Pregel-inspired vertex-centric computation models for web-scale graph analytics. "
            "Our novel edge-cut partitioning strategy reduces cross-machine communication by "
            "60% compared to PowerGraph and achieves near-linear scaling on clusters up to "
            "1,024 nodes."
        ),
        "authors": [
            {"name": "Prof. James O'Brien","order": 1},
            {"name": "Prof. Marcus Weber", "order": 2},
        ],
        "topics": [
            {"name": "Distributed Systems", "relevance": "primary"},
            {"name": "Data Science",        "relevance": "secondary"},
        ],
    },
    {
        "title": "Human-AI Collaboration in Creative Work",
        "year": 2023,
        "abstract": (
            "A mixed-methods study of how creative professionals co-create with generative AI "
            "systems across music, writing, and visual design. We identify trust, agency, and "
            "attribution as central tension points and propose a collaboration design framework."
        ),
        "authors": [
            {"name": "Dr. Sarah Kim",   "order": 1},
            {"name": "Dr. Lena Fischer","order": 2},
        ],
        "topics": [
            {"name": "Human-Computer Interaction", "relevance": "primary"},
            {"name": "Artificial Intelligence",    "relevance": "secondary"},
        ],
    },
    {
        "title": "Secure Aggregation in Federated Networks",
        "year": 2023,
        "abstract": (
            "Cryptographic protocols for gradient aggregation in federated learning that "
            "prevent honest-but-curious servers from learning individual updates. We achieve "
            "sub-linear communication overhead using homomorphic commitments and prove "
            "security under the DDH assumption."
        ),
        "authors": [
            {"name": "Dr. Fatima Al-Rashid", "order": 1},
            {"name": "Prof. Omar Hassan",    "order": 2},
        ],
        "topics": [
            {"name": "Cybersecurity",   "relevance": "primary"},
            {"name": "Machine Learning","relevance": "secondary"},
        ],
    },
    {
        "title": "Genomic Variant Calling at Population Scale",
        "year": 2022,
        "abstract": (
            "A scalable cloud-native pipeline integrating BWA-MEM2, GATK4, and DeepVariant "
            "for whole-genome sequencing at population scale. Automated quality control and "
            "parallel joint genotyping reduce wall-clock time by 5x compared to the GATK "
            "Best Practices pipeline."
        ),
        "authors": [
            {"name": "Dr. Priya Nair",   "order": 1},
            {"name": "Dr. Lena Fischer", "order": 2},
        ],
        "topics": [
            {"name": "Bioinformatics",    "relevance": "primary"},
            {"name": "Distributed Systems","relevance": "secondary"},
            {"name": "Data Science",      "relevance": "secondary"},
        ],
    },
    {
        "title": "Graph Neural Networks for Molecular Property Prediction",
        "year": 2023,
        "abstract": (
            "Message-passing neural networks on molecular graphs for predicting drug-protein "
            "binding affinity, aqueous solubility, and ADMET toxicity. Our architecture "
            "achieves state-of-the-art results on MoleculeNet benchmarks and enables "
            "efficient virtual screening of billion-compound libraries."
        ),
        "authors": [
            {"name": "Dr. Elena Zhao",    "order": 1},
            {"name": "Dr. Charlie Davis", "order": 2},
            {"name": "Prof. Raj Patel",   "order": 3},
        ],
        "topics": [
            {"name": "Artificial Intelligence", "relevance": "primary"},
            {"name": "Machine Learning",        "relevance": "primary"},
            {"name": "Bioinformatics",          "relevance": "secondary"},
        ],
    },
]


# ── Seed function ──────────────────────────────────────────────────────────────

def seed_database():
    session = db.get_session()
    try:
        print("Clearing existing graph...")
        session.run("MATCH (n) DETACH DELETE n")

        print("Creating Topic nodes...")
        for name in TOPICS:
            session.run("CREATE (:Topic {name: $name})", name=name)

        print("Creating Researcher nodes...")
        for r in RESEARCHERS:
            session.run(
                "CREATE (:Researcher {name: $name, affiliation: $affiliation})",
                name=r["name"], affiliation=r["affiliation"]
            )

        print("Creating Paper nodes and relationships...")
        for p in PAPERS:
            # MERGE paper to handle co-authored papers without duplication
            session.run(
                """
                MERGE (p:Paper {title: $title})
                ON CREATE SET p.year = $year, p.abstract = $abstract
                """,
                title=p["title"], year=p["year"], abstract=p["abstract"]
            )

            # Create [:AUTHORED] relationships with order property
            for author in p["authors"]:
                session.run(
                    """
                    MATCH (r:Researcher {name: $author_name})
                    MATCH (p:Paper {title: $title})
                    MERGE (r)-[:AUTHORED {order: $order}]->(p)
                    """,
                    author_name=author["name"],
                    title=p["title"],
                    order=author["order"]
                )

            # Create [:ABOUT] relationships with relevance property
            for topic in p["topics"]:
                session.run(
                    """
                    MATCH (p:Paper {title: $title})
                    MATCH (t:Topic {name: $topic_name})
                    MERGE (p)-[:ABOUT {relevance: $relevance}]->(t)
                    """,
                    title=p["title"],
                    topic_name=topic["name"],
                    relevance=topic["relevance"]
                )

        print("Database seeded successfully!")
        print(f"  {len(RESEARCHERS)} researchers")
        print(f"  {len(PAPERS)} papers")
        print(f"  {len(TOPICS)} topics")
        institutions = {r['affiliation'] for r in RESEARCHERS}
        print(f"  {len(institutions)} institutions")

    except Exception as e:
        print(f"Error seeding database: {e}")
        raise
    finally:
        session.close()
        db.close()


if __name__ == "__main__":
    seed_database()
