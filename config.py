import os
import sys

from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()

        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:2b")
        self.OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.MIN_CURATION_SCORE = int(os.getenv("MIN_CURATION_SCORE", "60"))
        self.MAX_PRODUCTS_PER_RUN = int(os.getenv("MAX_PRODUCTS_PER_RUN", "5"))
        self.DB_PATH = os.path.join("data", "pipeline.db")
        self.OUTPUT_DIR = os.path.join("data", "output")
        self.CANDIDATES_CSV = os.path.join("data", "candidates.csv")

    def validate(self):
        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            print(
                "ERRO: LLM_PROVIDER=anthropic mas ANTHROPIC_API_KEY não definida. "
                "Preencha a chave no .env ou use LLM_PROVIDER=ollama."
            )
            sys.exit(1)

        if self.LLM_PROVIDER == "ollama":
            import urllib.request
            import urllib.error
            try:
                urllib.request.urlopen(self.OLLAMA_BASE_URL, timeout=5)
            except urllib.error.URLError:
                print(
                    f"ERRO: Ollama não está rodando em {self.OLLAMA_BASE_URL}. "
                    "Inicie com: ollama serve"
                )
                sys.exit(1)

        if self.LLM_PROVIDER not in ("ollama", "anthropic"):
            print(f"ERRO: LLM_PROVIDER '{self.LLM_PROVIDER}' inválido. Use 'ollama' ou 'anthropic'.")
            sys.exit(1)


def load_config() -> Config:
    config = Config()
    config.validate()
    return config
