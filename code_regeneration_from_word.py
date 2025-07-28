import os
from docx import Document

def recreate_files_from_docx(docx_path, output_dir):
    doc = Document(docx_path)
    current_file_path = None
    current_content = []

    for para in doc.paragraphs:
        text = para.text.strip()

        # Detect start of a new file
        if text.startswith("File: "):
            # Save previous file if any
            if current_file_path and current_content:
                save_file(current_file_path, current_content, output_dir)
                current_content = []

            # Get new file path
            current_file_path = text.replace("File: ", "").strip()

        elif text == "-" * 50:
            # End of current file
            if current_file_path and current_content:
                save_file(current_file_path, current_content, output_dir)
                current_file_path = None
                current_content = []
        else:
            if current_file_path:
                current_content.append(para.text)

    # Save the last file
    if current_file_path and current_content:
        save_file(current_file_path, current_content, output_dir)

    print(f"All files reconstructed in: {output_dir}")

def save_file(original_path, lines, output_dir):
    # Recreate the relative structure inside output_dir
    relative_path = os.path.relpath(original_path, start=r"C:\Users\yuval\PycharmProjects\ArcSpatialDB")
    new_path = os.path.join(output_dir, relative_path)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)

    try:
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"Saved: {new_path}")
    except Exception as e:
        print(f"Failed to write {new_path}: {e}")

# Example usage:
docx_input = r"C:\Users\yuval\PycharmProjects\ArcSpatialDB\code_files_collected.docx"
rebuild_output_dir = r"C:\Users\yuval\PycharmProjects\ArcSpatialDB_Rebuilt"

recreate_files_from_docx(docx_input, rebuild_output_dir)
