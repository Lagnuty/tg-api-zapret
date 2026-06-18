from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    source = Path("docs/mtproto-importance-layers.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    layer = data["layers"]["1"]
    functions = [
        definition
        for definition in layer["definitions"]
        if definition["category"] == "function"
    ]
    implemented = []
    for definition in functions:
        implemented.append(
            {
                "layer": 1,
                "implemented": True,
                "implementation": "dynamic_mtproto_layer_dispatcher",
                "endpoints": [
                    "GET /mtproto/layers/1/functions",
                    "POST /mtproto/layers/1/invoke",
                    "POST /raw/invoke",
                    "POST /rpc method=raw.invoke",
                ],
                **definition,
            }
        )

    output = {
        "source": source.as_posix(),
        "layer": 1,
        "function_count": len(functions),
        "implemented_count": len(implemented),
        "implementation_note": (
            "All Layer 1 request-functions are implemented through the dynamic "
            "MTProto layer dispatcher. Individual functions are executed by "
            "callable_path with kwargs."
        ),
        "functions": implemented,
    }
    Path("docs/implemented-layer-1-functions.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    Path("docs/implemented-layer-1-functions.md").write_text(
        render_markdown(output),
        encoding="utf-8",
    )
    print(f"implemented_layer_1_functions={len(implemented)}")


def render_markdown(output: dict) -> str:
    lines = [
        "# Implemented MTProto Layer 1 Functions",
        "",
        f"Source: `{output['source']}`.",
        f"Layer: `{output['layer']}`.",
        f"Implemented functions: `{output['implemented_count']}` / `{output['function_count']}`.",
        "",
        output["implementation_note"],
        "",
        "## Endpoints",
        "",
        "- `GET /mtproto/layers/1/functions`",
        "- `POST /mtproto/layers/1/invoke`",
        "- `POST /raw/invoke`",
        "- `POST /rpc` with `method=raw.invoke`",
        "",
        "## Functions",
        "",
        "| Implemented | Namespace | Function | Callable Path | Signature |",
        "|---|---|---|---|---|",
    ]
    for item in output["functions"]:
        signature = item["constructor_signature"].replace("|", "\\|")
        lines.append(
            "| "
            f"`{item['implemented']}` | "
            f"`{item['namespace']}` | "
            f"`{item['name']}` | "
            f"`{item['callable_path']}` | "
            f"`{signature}` |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()

