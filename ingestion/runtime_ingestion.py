import json
import os
import tempfile

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from ingestion.pdf_parser import parse_pdf
from ingestion.router import route_elements
from ingestion.table_processor import process_tables
from ingestion.chunker import build_chunks

MODEL_NAME = "BAAI/bge-base-en"


def ingest_pdf_to_runtime(pdf_path: str) -> dict:

    with tempfile.TemporaryDirectory(prefix="runtime_ingestion_") as work_dir:

        parsed_path = os.path.join(work_dir, "parsed_elements.json")
        text_elements_path = os.path.join(work_dir, "text_elements.json")
        table_elements_path = os.path.join(work_dir, "table_elements.json")
        tables_raw_path = os.path.join(work_dir, "tables_raw.json")
        tables_index_path = os.path.join(work_dir, "tables_index.json")
        chunks_path = os.path.join(work_dir, "chunks.json")
        missing_images_path = os.path.join(work_dir, "image_semantics.json")


        # -------------------------------------------------
        # STEP 1: Parse PDF
        # -------------------------------------------------

        parse_pdf(
            pdf_path=pdf_path,
            output_path=parsed_path
        )


        # -------------------------------------------------
        # STEP 2: Route elements
        # -------------------------------------------------

        route_elements(
            input_path=parsed_path,
            output_dir=work_dir
        )


        # -------------------------------------------------
        # STEP 3: Process tables
        # -------------------------------------------------

        process_tables(
            input_path=table_elements_path,
            raw_output_path=tables_raw_path,
            index_output_path=tables_index_path,
        )


        # -------------------------------------------------
        # STEP 4: Build chunks
        # -------------------------------------------------

        build_chunks(
            text_path=text_elements_path,
            tables_index_path=tables_index_path,
            images_path=missing_images_path,
            output_path=chunks_path,
        )


        # -------------------------------------------------
        # STEP 5: Load chunks
        # -------------------------------------------------

        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)


        with open(tables_raw_path, "r", encoding="utf-8") as f:
            tables_raw = json.load(f)


        # -------------------------------------------------
        # STEP 6: Convert chunks → texts
        # -------------------------------------------------

        texts = []
        metadata = []

        for chunk in chunks:

            text = chunk.get("text", "").strip()

            if not text:
                continue


            section = chunk.get("section", "")

            chunk_text = f"{section}\n{text}".strip()


            texts.append(chunk_text)


            metadata.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "section": section,
                    "pages": chunk.get("pages", []),
                    "tables": chunk.get("tables", []),
                    "images": chunk.get("images", []),
                    "chunk_text": chunk_text,
                }
            )


        # -------------------------------------------------
        # FIX: Better error message + debug info
        # -------------------------------------------------

        if len(texts) == 0:

            # Print debug info
            print("\n❌ DEBUG INFO:")
            print(f"parsed_elements exists: {os.path.exists(parsed_path)}")
            print(f"text_elements exists: {os.path.exists(text_elements_path)}")
            print(f"chunks exists: {os.path.exists(chunks_path)}")
            print(f"chunks count: {len(chunks)}")

            raise ValueError(
                "No text chunks extracted from uploaded PDF. "
                "This usually means parser or router did not extract text."
            )


        # -------------------------------------------------
        # STEP 7: Create embeddings
        # -------------------------------------------------

        model = SentenceTransformer(MODEL_NAME)


        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )


        dim = embeddings.shape[1]


        index = faiss.IndexFlatIP(dim)


        index.add(
            np.asarray(
                embeddings,
                dtype=np.float32
            )
        )


        return {

            "index": index,

            "metadata": metadata,

            "tables": tables_raw,

        }
