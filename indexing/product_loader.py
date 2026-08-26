import config
import logging
import json
import os


logger = logging.getLogger(__name__)

def load_products() -> list:
    path = os.path.join(config.DATA_DIR, "products.json")
    logger.info('开始读取产品库信息，路径：%s',path)
    try:
        with open(path,'r',encoding='utf-8')as f:
            products_list = json.load(f)
            logger.info(f'产品库信息读取成功')
            return products_list["products"]
    except Exception as e:
        logger.error('产品库信息读取失败,错误：%s,返回空列表',e)
        return []