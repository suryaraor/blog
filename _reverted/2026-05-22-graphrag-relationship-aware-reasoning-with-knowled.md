---
layout: default
title: "GraphRAG: Relationship-Aware Reasoning with Knowledge Graphs"
date: 2025-01-01
audio: /assets/audio/posts/2026-05-22-graphrag-relationship-aware-reasoning-with-knowledge-graphs.wav
---

# GraphRAG: Relationship-Aware Reasoning with Knowledge Graphs

You're about to learn how to supercharge reasoning in AI applications using relationships. We'll demystify Graph Databases, Neo4j, Relationship-Aware Reasoning, Agent Lookups, Knowledge Graphs, and Relational Data Mapping. Each concept gets a clear definition, a simple analogy, and a working code example. By the end, you'll know how to query and connect data using graph thinking instead of clunky joins. No jargon. No fluff. Just practical understanding you can apply today.

## Graph Databases: The Social Network for Your Data

A graph database stores data as nodes (things) and edges (connections). Think of it like a social network: people are nodes, friendships are edges. Unlike a traditional SQL table, a graph database makes relationships first-class citizens—you can traverse them without expensive JOIN operations.

Under the hood, graph databases use adjacency lists. Each node stores a list of its immediate neighbors. When you query a relationship (like "find all people who know Bob"), the database follows pointers between nodes instead of scanning entire tables. This makes relationship-heavy queries blazingly fast.

**Analogy**: Imagine a conference hall with name badges. In SQL, you'd create a "hall" table, a "people" table, and a "knows" table, then join them—like checking every badge against every other badge. In a graph database, you just look at Bob's badge and read the names of people he's connected to.

**Code example** (Neo4j's Cypher query language):
```cypher
// Find all people who know Bob
MATCH (p:Person)-[:KNOWS]->(b:Person {name: 'Bob'})
RETURN p.name
```
This returns the names of all nodes connected to Bob via a `KNOWS` edge. One hop, no joins.

## Neo4j: The Graph Database on Your Laptop

Neo4j is the most popular graph database. It's open-source, ACID-compliant, and uses a property graph model—nodes and edges can have key-value pairs (properties). You interact with it using Cypher, a declarative query language.

Under the hood, Neo4j stores data in a custom storage engine optimized for graph traversals. Each node and relationship is stored as a fixed-size record, with pointers to adjacent records. This means traversing a relationship is a pointer lookup, not a table scan—orders of magnitude faster than SQL for deep relationship queries.

**Analogy**: Imagine a business card with a list of "knows" on the back. Each name on that list is another card with its own list. Neo4j stores cards and their lists in a way that lets you flip through them instantly.

**Code example** (Python with Neo4j driver):
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

def find_connections(tx, name):
    result = tx.run("MATCH (p:Person {name: $name})-[:KNOWS]-(others) RETURN others.name", name=name)
    return [record["others.name"] for record in result]

with driver.session() as session:
    connections = session.execute_read(find_connections, "Alice")
    print(connections)  # ["Bob", "Charlie", "Diana"]
```
**Gotcha**: Neo4j tends to be slower than relational databases for non-relationship queries (like "what's the average age of all people?"). Use a graph database only when your data's value comes from its connections.

## Knowledge Graphs: The Encyclopedia with Footnotes

A knowledge graph is a graph database that models real-world entities and their relationships in a structured way. Every node represents a thing (a person, a place, a concept), every edge represents a semantic relationship ("works for," "born in," "expressed as"). Google's Knowledge Graph powers its search results—when you search for "Einstein," it shows his birth date, inventions, and quotes because everything links back to a single node.

Under the hood, knowledge graphs use ontologies—formal descriptions of entities and relationship types—to enforce consistency. Every relationship has a predicate (like `WORKS_FOR` or `BORN_IN`) that comes from a controlled vocabulary. This lets you query by meaning, not just keyword.

**Analogy**: Think of a knowledge graph as an encyclopedia where every article is a node, every cross-reference is an edge, and every cross-reference has a label like "see also: XX" instead of just "see also."

**Code example** (Cypher for a knowledge graph of movies and actors):
```cypher
// Find all actors born in the same city as a given director
MATCH (d:Director {name: "Spielberg"})-[:BORN_IN]->(city:City)
MATCH (actor:Actor)-[:BORN_IN]->(city)
RETURN actor.name
```
This demonstrates how a knowledge graph connects disparate entities (actors, directors, cities) through shared relationships.

## Relationship-Aware Reasoning: Thinking in Hops

Relationship-aware reasoning means using the structure of connections to draw inferences. Instead of asking "what's the value of X?" you ask "what paths exist between X and Y?" This is how recommendation systems decide "people who bought X also bought Y"—it's one hop in the graph.

Under the hood, relationship-aware reasoning uses graph traversal algorithms: breadth-first search (BFS) for shortest paths, depth-first search (DFS) for exploring deep connections, and PageRank for finding influential nodes. For GraphRAG, we use vector embeddings *conditioned on the graph structure*—a node's embedding captures not just its properties but its neighborhood.

**Analogy**: You're at a party. Relationship-aware reasoning is not just knowing someone's name; it's knowing who they talk to, who they've introduced you to, and who they've never met. That social map helps you predict introductions and avoid awkward run-ins.

**Non-obvious insight**: Most graph learning models (like Graph Convolutional Networks) assume locally connected structures. A node with high degree (many connections) can dominate its neighbor's embeddings, washing out individuality. To counter this, some architectures sample a fixed number of neighbors per node, not all of them.

**Code example** (Python with PyTorch Geometric for graph convolution):
```python
import torch
import torch.nn.functional as F
from torch_geometric.nn import GCNConv

class GCN(torch.nn.Module):
    def __init__(self, num_features, num_classes):
        super().__init__()
        self.conv1 = GCNConv(num_features, 16)
        self.conv2 = GCNConv(16, num_classes)

    def forward(self, data):
        x, edge_index = data.x, data.edge_index
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)
```
Here `edge_index` encodes the graph—it's a 2D list of pairs `[source, target]`. The model learns to aggregate information from a node's neighbors at each layer, enabling relationship-aware reasoning.

## Agent Lookups: Asking the Graph a Question

An agent lookup is when a software agent (like a chatbot or automation script) queries a knowledge graph to answer a user's request. The agent translates a natural language question into a graph query, executes it, and returns a structured answer.

Under the hood, the agent uses entity linking to map words in the question to graph nodes, then relation extraction to match verbs to edge types. For example: "Who directed Inception?" becomes `MATCH (d:Director)-[:DIRECTED]->(m:Movie {title: 'Inception'}) RETURN d.name`.

**Analogy**: A librarian who's not just good at finding books—they can follow the "see also" references to find every book related to your topic. The agent is the librarian; the knowledge graph is the card catalog.

**Code example** (pseudo-agent with LangChain and Neo4j):
```python
from langchain.agents import create_cypher_agent
from langchain_community.graphs import Neo4jGraph

graph = Neo4jGraph(url="bolt://localhost:7687", username="neo4j", password="password")
agent = create_cypher_agent(llm=your_llm, graph=graph, verbose=True)
response = agent.run("Who starred in The Matrix?")
# Under the hood: MATCH (a:Actor)-[:ACTED_IN]->(m:Movie {title: 'The Matrix'}) RETURN a.name
print(response)  # Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss
```
**Gotcha**: Agent lookups fail when the knowledge graph is incomplete or the question contains synonyms not in the ontology. Always have a fallback "I don't know" response.

## Relational Data Mapping: Turning Tables into Graphs

Relational data mapping is the process of converting data from SQL tables (rows and columns) into a graph structure (nodes and edges). You decide which table becomes which node type, and which foreign keys become edges.

Under the hood, mapping involves denormalizing joins into graph edges. For example, an `orders` table with a `customer_id` column becomes a `PURCHASED` edge from a Customer node to an Order node. You lose some SQL flexibility (like aggregate functions on joins) but gain traversal speed for connection queries.

**Analogy**: Imagine you have a spreadsheet of employees (rows) and a separate spreadsheet of departments (rows). With SQL, you'd join them by department ID. With a graph, you'd create Employee nodes and Department nodes, and add a `WORKS_IN` edge from each employee to their department. Same information, different structure.

**Code example** (Python with pandas + py2neo for mapping):
```python
import pandas as pd
from py2neo import Graph, Node, Relationship

graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

# Load data
orders = pd.read_csv("orders.csv")  # columns: order_id, customer_id, total
customers = pd.read_csv("customers.csv")  # columns: customer_id, name

# Create nodes
cust_nodes = {}
for _, row in customers.iterrows():
    n = Node("Customer", name=row["name"], id=row["customer_id"])
    graph.create(n)
    cust_nodes[row["customer_id"]] = n

# Create edges
for _, row in orders.iterrows():
    order_node = Node("Order", total=row["total"], id=row["order_id"])
    graph.create(order_node)
    edge = Relationship(cust_nodes[row["customer_id"]], "PURCHASED", order_node)
    graph.create(edge)
```
**Non-obvious insight**: One-to-many relationships (a customer with many orders) become one-to-many edges. But many-to-many relationships (products in many orders) become intermediate "line-item" nodes. Overlook this and your graph will have unintended fan-out queries.

## Comparison Table: The Concepts in One View

| Concept | Purpose | Example Tool | Key Strength |
|---|---|---|---|
| Graph Database | Store data as nodes and edges | Neo4j, Amazon Neptune | Fast relationship traversal |
| Neo4j | Popular graph database with Cypher | Neo4j | ACID compliance, easy setup |
| Knowledge Graph | Encode real-world semantics | Wikidata, Google Knowledge Graph | Structured, queryable ontology |
| Relationship-Aware Reasoning | Use graph structure for inference | PyTorch Geometric, DGL | Captures local context |
| Agent Lookups | Translate NL to graph queries | LangChain + Cypher | Power chatbot & automation |
| Relational Data Mapping | Convert SQL tables to graph | py2neo, Apache AGE | Preserves relationships |

## Key Takeaways

- Graph databases **store nodes and edges**; they excel at queries that traverse relationships.
- Neo4j is a **practical graph database**; use Cypher like SQL for graphs.
- Knowledge graphs add **semantic structure**; entities have typed relationships.
- Relationship-aware reasoning **uses neighborhood information** for predictions.
- Agent lookups **bridge natural language and graph queries** ; handle missing data gracefully.
- Relational data mapping **turns tables into graphs**; watch for many-to-many relationships.
- Always ask: does the value come from being able to walk the graph? If yes, use GraphRAG. If not, maybe stick with SQL.
