"""
rag/build_kb.py — End-to-end Knowledge Base build pipeline.

Usage:
    python -m rag.build_kb                  # Full rebuild
    python -m rag.build_kb --skip-chunks    # Use cached chunks, just re-index
    python -m rag.build_kb --verify         # Build then run verification queries

Pipeline:
    1. Load raw documents from data/raw/
    2. Clean each document
    3. Chunk into overlapping segments with metadata
    4. Save chunks to data/processed/chunks/
    5. Embed and index in ChromaDB
    6. (Optional) Run verification queries
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("build_kb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build the AI Dermatology Assistant knowledge base."
    )
    parser.add_argument(
        "--skip-chunks",
        action="store_true",
        help="Skip loading/cleaning/chunking; load from existing data/processed/chunks/.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run sample retrieval queries after building.",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Delete existing ChromaDB collection before rebuilding.",
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Override the raw documents directory.",
    )
    return parser.parse_args()


def run_pipeline(
    skip_chunks: bool = False,
    verify: bool = False,
    force_rebuild: bool = False,
    raw_dir: str | None = None,
) -> None:
    """Execute the full KB build pipeline."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

    console = Console()
    console.print(Panel.fit(
        "[bold cyan]AI Dermatology Assistant — Knowledge Base Builder[/bold cyan]",
        border_style="cyan",
    ))

    start = time.time()

    # ── Step 0: imports ───────────────────────────────────────────────────────
    from rag.config import cfg
    from rag.loaders import load_documents
    from rag.cleaner import full_clean
    from rag.chunker import DocumentChunker
    from rag.persistence import save_chunks, load_chunks, chunks_exist
    from rag.vectorstore import build_vectorstore, delete_collection, collection_info

    raw_path = Path(raw_dir) if raw_dir else cfg.RAW_DIR

    # ── Step 1 & 2 & 3: Load → Clean → Chunk (or load from cache) ────────────
    if skip_chunks and chunks_exist():
        console.print("\n[yellow]⚡ Skipping chunking — loading cached chunks …[/yellow]")
        documents = load_chunks()
        if not documents:
            console.print("[red]No cached chunks found. Run without --skip-chunks.[/red]")
            sys.exit(1)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            # Load
            task_load = progress.add_task("[cyan]1/3  Loading raw documents …", total=None)
            raw_docs = load_documents(raw_path)
            progress.update(task_load, description=f"[green]1/3  Loaded {len(raw_docs)} documents ✓")
            progress.stop_task(task_load)

            if not raw_docs:
                console.print(
                    f"\n[red]✗ No documents found in '{raw_path}'.\n"
                    "Add PDF/DOCX/TXT files to data/raw/ sub-folders and re-run.[/red]"
                )
                sys.exit(1)

            # Clean
            task_clean = progress.add_task("[cyan]2/3  Cleaning documents …", total=len(raw_docs))
            for raw_doc in raw_docs:
                raw_doc.text = full_clean(raw_doc.text)
                progress.advance(task_clean)
            progress.update(task_clean, description="[green]2/3  Cleaning done ✓")

            # Chunk
            task_chunk = progress.add_task("[cyan]3/3  Chunking …", total=len(raw_docs))
            chunker = DocumentChunker()
            documents = chunker.chunk_all(raw_docs)
            progress.advance(task_chunk, len(raw_docs))
            progress.update(task_chunk, description=f"[green]3/3  {len(documents)} chunks created ✓")

        # Save chunks to disk
        console.print("\n[cyan]💾  Saving chunks to data/processed/chunks/ …[/cyan]")
        saved_path = save_chunks(documents)
        console.print(f"[green]    Saved → {saved_path}[/green]")

    # ── Step 4: Embed & Index ─────────────────────────────────────────────────
    if force_rebuild:
        console.print("\n[yellow]🗑   Force-rebuild: deleting existing collection …[/yellow]")
        try:
            delete_collection()
        except Exception:
            pass  # Collection may not exist yet

    console.print(f"\n[cyan]🔢  Embedding {len(documents)} chunks and indexing in ChromaDB …[/cyan]")
    console.print("[dim]    (First run downloads the embedding model — this may take a minute)[/dim]")

    vectorstore = build_vectorstore(documents)
    info = collection_info()
    console.print(
        f"[green]✓   ChromaDB ready — {info['total_vectors']} vectors in "
        f"collection '{info['collection_name']}'[/green]"
    )

    # ── Step 5 (Optional): Verification ──────────────────────────────────────
    if verify:
        _run_verification(vectorstore, console)

    elapsed = time.time() - start
    console.print(
        Panel.fit(
            f"[bold green]✅  Knowledge base built in {elapsed:.1f}s[/bold green]",
            border_style="green",
        )
    )


def _run_verification(vectorstore, console) -> None:
    """Run sample queries and print results to verify retrieval quality."""
    from rich.table import Table

    SAMPLE_QUERIES = [
        ("Psoriasis symptoms",          "What are the symptoms of psoriasis?"),
        ("Acne treatment",              "How is acne vulgaris treated?"),
        ("Eczema causes",               "What causes atopic dermatitis?"),
        ("Melanoma warning signs",      "What are the warning signs of melanoma?"),
        ("Fungal skin infection",       "How to treat tinea / fungal skin infection?"),
    ]

    console.print("\n[bold cyan]🔍  Verification — Sample Retrieval Queries[/bold cyan]")

    for label, query in SAMPLE_QUERIES:
        results = vectorstore.similarity_search(query, k=3)
        table = Table(title=f"Query: {label}", show_header=True, header_style="bold magenta")
        table.add_column("Chunk", style="dim", width=6)
        table.add_column("Disease", width=20)
        table.add_column("ICD", width=8)
        table.add_column("Source", width=30)
        table.add_column("Preview", width=60)

        for i, doc in enumerate(results, 1):
            table.add_row(
                str(i),
                doc.metadata.get("disease_category", "—"),
                doc.metadata.get("icd_code", "—"),
                doc.metadata.get("source_file", "—"),
                doc.page_content[:100].replace("\n", " ") + "…",
            )

        console.print(table)


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        skip_chunks=args.skip_chunks,
        verify=args.verify,
        force_rebuild=args.force_rebuild,
        raw_dir=args.raw_dir,
    )
