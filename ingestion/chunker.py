import json
import os


# -------------------------------
# LOAD HELPERS
# -------------------------------

def load_json(path):

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------
# MAIN CHUNKER
# -------------------------------

def build_chunks(
    text_path,
    tables_index_path,
    images_path,
    output_path
):

    text_elements = load_json(text_path)
    tables_index = load_json(tables_index_path)
    images = load_json(images_path)


    chunks = []


    current_section = None
    current_text = []
    current_pages = set()

    chunk_id = 0


    # -------------------------------
    # FLUSH FUNCTION
    # -------------------------------

    def flush_chunk():

        nonlocal chunk_id, current_section, current_text, current_pages


        if not current_section or not current_text:
            return


        pages = sorted(list(current_pages))


        attached_tables = [

            t["id"]

            for t in tables_index

            if t.get("page") in pages

        ]


        attached_images = [

            {

                "page": img.get("page"),

                "caption": img.get("caption")

            }

            for img in images

            if img.get("page") in pages

        ]


        chunk_id += 1


        chunks.append({

            "chunk_id": f"chunk_{chunk_id:03d}",

            "section": current_section,

            "pages": pages,

            "text": "\n".join(current_text),

            "tables": attached_tables,

            "images": attached_images

        })


        # Reset
        current_text = []
        current_pages = set()


    # -------------------------------
    # ITERATE ELEMENTS
    # -------------------------------

    for el in text_elements:


        el_type = el.get("type")

        el_text = el.get("text", "").strip()

        el_page = el.get("page")


        if not el_text:
            continue


        # --------------------------------
        # NORMAL TITLE
        # --------------------------------

        if el_type == "Title":

            flush_chunk()

            current_section = el_text

            continue


        # --------------------------------
        # CRITICAL FIX:
        # Handle HF parser not detecting Title
        # --------------------------------

        if not current_section:

            current_section = el_text

            continue


        # --------------------------------
        # NORMAL TEXT
        # --------------------------------

        if el_type in ["NarrativeText", "Text", "ListItem", "Header", "Footer"]:

            current_text.append(el_text)

            if el_page is not None:
                current_pages.add(el_page)


    # Flush last chunk
    flush_chunk()


    # -------------------------------
    # SAVE OUTPUT
    # -------------------------------

    with open(output_path, "w", encoding="utf-8") as f:

        json.dump(chunks, f, indent=2, ensure_ascii=False)


# -------------------------------
# CLI ENTRYPOINT
# -------------------------------

if __name__ == "__main__":

    build_chunks(

        text_path="data/processed/text_elements.json",

        tables_index_path="data/processed/tables_index.json",

        images_path="data/processed/image_semantics.json",

        output_path="data/processed/chunks.json"

    )
