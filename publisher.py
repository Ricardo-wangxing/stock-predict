import pika
import json
import fire
from loguru import logger
from stock_predict.stock_spider.config import config


parameters = (
    pika.ConnectionParameters(host=config["RABBITMQ_HOST"], port=config["RABBITMQ_PORT"],heartbeat=0)
)

conn = pika.BlockingConnection(parameters)
channel = conn.channel()

def publish_get_hs300_daily():
    payload = {
        'task':'hs300_daily'
    }
    logger.info("publish to queue {} get_hs300_daily".format(config['routing_key']))
    channel.basic_publish(exchange='', routing_key=config['routing_key'], body=bytes(json.dumps(payload), "utf-8"))

def publish_get_hs300_all():
    payload = {
        'task':'hs300_all'
    }
    logger.info("publish to queue {} get_hs300_all".format(config['routing_key']))
    channel.basic_publish(exchange='', routing_key=config['routing_key'], body=bytes(json.dumps(payload), "utf-8"))

def publish_daily_update_etf():
    payload = {
        'policy_stock_pool':config["policy_stock_pool"],
        'task':'daily_update_etf'
    }
    logger.info("publish to queue {} daily_update_etf".format(config['routing_key']))
    channel.basic_publish(exchange='', routing_key=config['routing_key'], body=bytes(json.dumps(payload), "utf-8"))    

def publish_write_stock(code):
    payload = {
        'code':code,
        'task':'write_stock'
    }
    logger.info("publish to queue {} write_stock".format(config['routing_key']))
    channel.basic_publish(exchange='', routing_key=config['routing_key'], body=bytes(json.dumps(payload), "utf-8"))    


if __name__ == "__main__":
    fire.Fire()
