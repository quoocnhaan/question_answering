import bz2
import csv
import xml.etree.ElementTree as ET


def extract_wiki_dump(input_bz2, output_csv):
    """
    Streams a compressed Wikipedia XML dump and extracts pages to a CSV.
    """
    print(f"Reading from: {input_bz2}")
    print(f"Writing to: {output_csv}")

    # Open the BZ2 stream and the output CSV
    with (
        bz2.open(input_bz2, "rt", encoding="utf-8") as xml_file,
        open(output_csv, "w", newline="", encoding="utf-8") as csv_file,
    ):
        writer = csv.writer(csv_file)
        # Define CSV headers
        writer.writerow(["page_id", "title", "text"])

        # iterparse() streams the XML, emitting events as tags open/close
        context = ET.iterparse(xml_file, events=("end",))

        page_id = None
        title = None
        text = None

        for event, elem in context:
            # Wikipedia XML uses namespaces (e.g., {http://www.mediawiki.org/xml/export-0.11/}title)
            # We split by '}' to grab just the tag name and ignore the namespace
            tag = elem.tag.split("}")[-1]

            if tag == "title":
                title = elem.text

            elif tag == "id" and page_id is None:
                # A <page> contains its own <id> and a nested <revision> which also has an <id>.
                # Capturing it while page_id is None ensures we only grab the primary Page ID.
                page_id = elem.text

            elif tag == "text":
                text = elem.text

            elif tag == "page":
                # Once the </page> closing tag is reached, write the data row
                if title and text:
                    writer.writerow([page_id, title, text])

                # Reset variables for the next page
                page_id = None
                title = None
                text = None

                # CRITICAL: Clear the element from memory to prevent RAM overflow
                elem.clear()

    print("Extraction complete!")


# Execute the function
file_path = "../data/raw/viwiki-2026-05-01-p1p19961822.xml.bz2"
output_path = "../data/clean/viwiki.csv"

extract_wiki_dump(file_path, output_path)
