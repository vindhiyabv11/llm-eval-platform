import json
import sys

src, dst = sys.argv[1], sys.argv[2]
NA = "The documents do not contain the answer; the assistant should abstain or say it does not know."

with open(src, encoding="utf-8") as f, open(dst, "w", encoding="utf-8") as o:
    for line in f:
        line = line.strip()
        if not line:
            continue
        q = json.loads(line)
        expected = q["reference_answer"] if q["answerable"] else NA
        o.write(json.dumps({
            "id": q["id"],
            "input": q["question"],
            "expected": expected,
            "tags": [q["type"]],
        }) + "\n")