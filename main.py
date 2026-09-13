import sys

from config import Config, load_config
from storage import init_db
import research
import curation
import copy_generator
import publish


def main() -> None:
    print("=" * 60)
    print("Amazon Listing Automation Pipeline")
    print("=" * 60)

    try:
        config = load_config()
    except SystemExit:
        sys.exit(1)

    init_db(config.DB_PATH)

    stages = [
        ("pesquisa", research.run),
        ("curadoria", curation.run),
        ("copy", copy_generator.run),
        ("publicacao", publish.run),
    ]

    for stage_name, stage_fn in stages:
        try:
            stage_fn(config)
        except Exception as e:
            print(f"[{stage_name}] ERRO FATAL na etapa: {e}")
            sys.exit(1)

    print("=" * 60)
    print("Pipeline concluído com sucesso.")
    print("=" * 60)


if __name__ == "__main__":
    main()
