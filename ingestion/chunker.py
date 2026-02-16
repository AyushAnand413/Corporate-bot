import json
import os


def load_json(path):

    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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


    chunk_id = 0


    current_section = None
    current_text = []
    current_pages = set()


    def flush_chunk():

        nonlocal chunk_id, current_section, current_text, current_pages


        if not current_text:
            return


        chunk_id += 1


        chunks.append({

            "chunk_id": f"chunk_{chunk_id:03d}",

            "section": current_section or "Document",

            "pages": sorted(list(current_pages)),

            "text": "\n".join(current_text),

            "tables": [],

            "images": []

        })


        current_text.clear()
        current_pages.clear()


    for el in text_elements:


        el_type = el.get("type")

        text = el.get("text", "").strip()

        page = el.get("page")


        if not text:
            continue


        # treat title normally
        if el_type == "Title":

            flush_chunk()

            current_section = text

            continue


        # treat ANY text-like element as content
        if el_type in [

            "NarrativeText",
            "Text",
            "CompositeElement",
            "ListItem",
            "Header",
            "Footer",
            "UncategorizedText"

        ]:

            if not current_section:
                current_section = "Document"

            current_text.append(text)

            if page is not None:
                current_pages.add(page)


    flush_chunk()


    with open(output_path, "w", encoding="utf-8") as f:

        json.dump(chunks, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":

    build_chunks(

        text_path="data/processed/text_elements.json",

        tables_index_path="data/processed/tables_index.json",

        images_path="data/processed/image_semantics.json",

        output_path="data/processed/chunks.json"

    )
