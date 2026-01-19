import subprocess
import tempfile
import os

def extract_text(image_path: str) -> str:
    """
    Runs Tesseract OCR on an image and returns extracted text.

    Returns: str
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tsv") as tsv:
        tsv_path = tsv.name

    subprocess.run(
        [
            "tesseract",
            image_path,
            tsv_path.replace(".tsv", ""),
            "-c",
            "tessedit_create_tsv=1"
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    
    #words = []
    data = []
    with open(tsv_path, encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            # print(line)

            # get only the words
            # parts = line.strip().split("\t")
            #if len(parts) >= 12 and parts[11].strip():
                #words.append(parts[11].strip())

            parts = line.strip().split("\t")
            if len(parts) >= 12 and parts[11].strip():
                dic = {
                    "text": parts[11].strip(),
                    "x": int(parts[6]),
                    "y": int(parts[7]),
                    "w": int(parts[8]),
                    "h": int(parts[9]),
                    "conf": float(parts[10]),
                    "line": (int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]))
                }
                data.append(dic)
                
    return data
