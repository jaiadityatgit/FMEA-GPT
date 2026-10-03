"""CLI tool to query the FMEA-GPT aerospace RAG knowledge base."""
import argparse
import json
import sys
from .config import RAGConfig
from .retriever import AerospaceRetriever


def print_banner():
    print("=" * 80)
    print("           FMEA-GPT AEROSPACE KNOWLEDGE RETRIEVAL CLI")
    print("=" * 80)


def display_results(query: str, results: list):
    print(f"\nQuery: \"{query}\"")
    print(f"Retrieved: {len(results)} passage(s)\n")
    print("-" * 80)

    if not results:
        print("  [No matching passages found. Try a different query or check index.]")
        print("-" * 80)
        return

    for rank, res in enumerate(results, start=1):
        print(f"[{rank}] RELEVANCE: {res.similarity_score * 100:.1f}%  |  Distance: {res.distance:.4f}")
        print(f"    Source Document : {res.source_document} (Page {res.page_number})")
        print(f"    Document Title  : {res.doc_title}")
        print(f"    Publisher       : {res.publisher}")
        print(f"    Document Type   : {res.document_type}")
        print(f"    Chunk ID        : {res.chunk_id}")
        print("    " + "-" * 74)
        print("    Text Passage:")
        for line in res.text.strip().splitlines():
            print(f"      {line}")
        print("-" * 80)


def main():
    parser = argparse.ArgumentParser(description="Query the FMEA-GPT ChromaDB vector knowledge base.")
    parser.add_argument("query", nargs="*", help="The search query or question to retrieve passages for.")
    parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of passages to retrieve (default: 5).")
    parser.add_argument("--doc-id", type=str, default=None, help="Filter by document ID (e.g., MIL-STD-1629A).")
    parser.add_argument("--publisher", type=str, default=None, help="Filter by publisher (e.g., FAA, NASA).")
    parser.add_argument("--json", action="store_true", help="Output results as structured JSON.")
    args = parser.parse_args()

    query_str = " ".join(args.query).strip() if args.query else ""
    if not query_str:
        print_banner()
        query_str = input("\nEnter aerospace engineering query: ").strip()
        if not query_str:
            print("Empty query. Exiting.")
            sys.exit(0)

    retriever = AerospaceRetriever()
    results = retriever.retrieve(
        query=query_str,
        top_k=args.top_k,
        doc_id=args.doc_id,
        publisher=args.publisher
    )

    if args.json:
        output = {
            "query": query_str,
            "top_k": args.top_k,
            "results_count": len(results),
            "results": [r.to_dict() for r in results]
        }
        print(json.dumps(output, indent=2))
    else:
        if args.query:
            print_banner()
        display_results(query_str, results)


if __name__ == "__main__":
    main()
