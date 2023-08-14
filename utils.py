import asyncio

from definitions import async_batch_fetch_definitions, load_definitions, save_definitions


def update_definitions_json():
    local_defs = load_definitions()
    api_defs = asyncio.run(async_batch_fetch_definitions(list(local_defs)))

    for word, defs in api_defs.items():
        if local_defs[word]["defs"] != defs["defs"] and defs["defs"]:
            print(f"Updating local definition for {word}.")
            local_defs[word]["defs"] = defs["defs"]

    save_definitions(local_defs)


def show_undefined_words():
    local_defs = load_definitions()
    for word, defs in local_defs.items():
        if not defs["defs"]:
            print(word)
