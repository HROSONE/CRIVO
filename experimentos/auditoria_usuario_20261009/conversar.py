"""Auditoria exploratória pela API publicada, com o histórico do frontend.

Não injeta memória, não troca modelos e não mede um conjunto cego.
Preserva também falhas HTTP e latências; o histórico inclui só envios aceitos.
"""
import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = "https://crivo-mauve.vercel.app/api/chat"


def run(session, messages):
    path = HERE / (session + ".json")
    data = json.loads(path.read_text()) if path.exists() else {
        "session": session, "endpoint": URL,
        "commit": "1e40650f28b5feb236ff619a182e8c833fe9068f",
        "method": "exploratório; continuidade escolhida após ler respostas; não avaliação cega",
        "turns": [],
    }
    history = [t["request"]["message"] for t in data["turns"]
               if t["status"] == 200 and "response" in t["result"]][-10:]
    for message in messages:
        sent = {"message": message, "history": history[-10:]}
        start = time.monotonic()
        request = urllib.request.Request(URL, data=json.dumps(sent, ensure_ascii=False).encode(),
                                         headers={"Content-Type": "application/json"})
        status = None
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                status = response.status
                raw = response.read().decode()
            result = json.loads(raw)
        except urllib.error.HTTPError as exc:
            status = exc.code
            raw = exc.read().decode(errors="replace")
            try:
                result = json.loads(raw)
            except ValueError:
                result = {"http_error": raw}
        except Exception as exc:
            result = {"error": type(exc).__name__ + ": " + str(exc)}
        turn = {"number": len(data["turns"]) + 1,
                "time_utc": datetime.now(timezone.utc).isoformat(),
                "request": sent, "status": status,
                "elapsed_seconds": round(time.monotonic() - start, 3), "result": result}
        data["turns"].append(turn)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"session": session, "turn": turn["number"], "message": message,
                          "status": status, "seconds": turn["elapsed_seconds"],
                          "response": result.get("response", result),
                          "id": result.get("id"), "generation": result.get("generation")},
                         ensure_ascii=False), flush=True)
        if status == 200 and "response" in result:
            history.append(message)
            history = history[-10:]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="JSON com session/messages; texto como dado, nunca shell")
    args = parser.parse_args()
    batches = json.loads(Path(args.input).read_text())
    for batch in batches:
        run(batch["session"], batch["messages"])
