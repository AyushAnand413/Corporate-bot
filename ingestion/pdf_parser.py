from unstructured.partition.pdf import partition_pdf
import json


def parse_pdf(pdf_path: str, output_path: str):

    # ==========================================
    # Production parser
    # Uses hi_res
    # OCR engine available but images disabled
    # ==========================================

    elements = partition_pdf(

        filename=pdf_path,

        strategy="hi_res",

        infer_table_structure=True,

        extract_images_in_pdf=False,   # disables image OCR

        include_page_breaks=False,

    )


    if not elements:

        raise ValueError("Parser failed: No elements extracted.")


    parsed_elements = []

    order = 0


    for el in elements:

        if hasattr(el, "text") and el.text and el.text.strip() == "":
            continue


        order += 1


        page = None

        if el.metadata and hasattr(el.metadata, "page_number"):
            page = el.metadata.page_number


        parsed_elements.append({

            "id": f"el_{order:06d}",

            "type": type(el).__name__,

            "text": el.text if hasattr(el, "text") else None,

            "page": page,

            "metadata": {

                "source": "unstructured",

                "raw_type": type(el).__name__

            }

        })


    with open(output_path, "w", encoding="utf-8") as f:

        json.dump(parsed_elements, f, indent=2, ensure_ascii=False)


    print(f"Parsed {len(parsed_elements)} elements successfully")
