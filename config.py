import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import sys


# Windows 终端默认 GBK，模型返回可能含 emoji 等 UTF-8 字符，强制 stdout/stderr 用 UTF-8
for _stream in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 加载 .env 文件，否则 os.getenv 读不到 DEEPSEEK_API_KEY
load_dotenv()

BASE_DIR = Path(os.getenv("BASE_DIR", Path(__file__).resolve().parent))
DATA_DIR = BASE_DIR/'data'
LOG_DIR = BASE_DIR/'logs'
INDEX_DIR = BASE_DIR/'FAISS_INDEX'

os.makedirs(DATA_DIR,exist_ok=True)
os.makedirs(LOG_DIR,exist_ok=True)
os.makedirs(INDEX_DIR,exist_ok=True)

#===== deepseek api配置 =====
# 注意：不设 sys.exit，key 为空也能 import，运行时再兜底
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = "deepseek-chat"

#===== embedding配置 =====
EMBEDDING_MODEL_NAME = "BAAI/bge-base-zh-v1.5"

# ========== HuggingFace 配置 ==========
# 模型首次加载会从 HF_ENDPOINT 下载并缓存到 HF_HOME；已有缓存命中不重复下载
HF_HOME = Path(os.getenv("HF_HOME", Path.home() / ".cache" / "huggingface"))
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("HF_ENDPOINT", HF_ENDPOINT)
# 强制离线：HF_OFFLINE=1 时只准用本地缓存
if os.getenv("HF_OFFLINE", "").strip().lower() in ("1", "true", "yes"):
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"

# ========== 最大循环轮数配置 ==========
MAX_iterations = 5

# ========== 检索配置 ==========
VECTOR_SEARCH_K = 5      # 向量检索取前5
BM25_SEARCH_K = 5        # BM25 检索取前5
RRF_K = 60               # RRF 融合常数
HYBRID_TOP_N = 5         # 融合后取前5
RERANKER_TOP_N = 3       # 重排后取前3
RERANKER_SCORE_THRESHOLD = 0.5  # 重排分数阈值
ENABLE_RERANKER = False  # v1 先关，v2 再开

# ========== 日志配置 ==========
LOG_LEVEL = "INFO"
from pythonjsonlogger.json import JsonFormatter
logging.basicConfig(
    level = getattr(logging,LOG_LEVEL,logging.INFO),
    handlers = [
        logging.FileHandler(os.path.join(LOG_DIR,"shop_assistant.log"),encoding='utf-8'),
        logging.StreamHandler()
    ]
)
# 给所有 handler 设置 JSON 格式
json_formatter = JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    json_ensure_ascii=False,  # 让中文日志以可读形式写入文件，而不是 \uXXXX 转义
)
for handler in logging.root.handlers:
    handler.setFormatter(json_formatter)

# ========== 静音第三方库日志（httpx/faiss/jieba 等自带的英文噪音） ==========
for _logger_name in (
    "httpx", "httpcore", "faiss", "jieba",
    "sentence_transformers", "transformers", "urllib3", "requests",
):
    logging.getLogger(_logger_name).setLevel(logging.WARNING)

#reranker 模型
RERANKER_MODEL_NAME = r"D:\huggingface_cache\models--BAAI--bge-reranker-base"