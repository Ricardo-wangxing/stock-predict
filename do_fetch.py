import pika
import traceback
import json
from loguru import logger
from datetime import date

from stock_predict.stock_spider.config import config
from stock_predict.stock_spider.db import *
from stock_predict.stock_spider.spider import *


def on_fetch_hs300_daily(ch, method_frame, properties, result):
    hs300_price_daily_update()
    logger.info("沪深300 {} 写入完成".format(date.today()))
    ch.basic_ack(method_frame.delivery_tag)

def on_fetch_hs300_all(ch, method_frame, properties, result):
    hs300_price_all_update()
    logger.info("沪深300全量写入完成")
    ch.basic_ack(method_frame.delivery_tag)    



# 1. 每日增量更新当前策略股票池 DONE
def on_fetch_daily_update_etf(ch, method_frame, properties, result):
    policy_stock_pool = result["policy_stock_pool"]
    policy_stock_pool.append(config["base"])
    etf_increment_update(policy_stock_pool)
    logger.info("ETF更新完成")
    ch.basic_ack(method_frame.delivery_tag)

# 2. 全量写入指定股票/基金的历史价格信息
def on_fetch_write_stock(ch, method_frame, properties, result):
    code = result["code"]
    etf_update([code])
    logger.info("{}全量写入完成".format(code))
    ch.basic_ack(method_frame.delivery_tag)


def on_message_callback(ch, method_frame, properties, body):
    try:
        result = json.loads(body.decode("utf-8"))

        if result["task"] == "hs300_daily":
            on_fetch_hs300_daily(ch, method_frame, properties, result)
        elif result["task"] == "hs300_all":
            on_fetch_hs300_all(ch, method_frame, properties, result)
        elif result["task"] == "daily_update_etf":
            on_fetch_daily_update_etf(ch, method_frame, properties, result)
        elif result["task"] == "write_stock":
            on_fetch_write_stock(ch, method_frame, properties, result)
        else:
            logger.error("task {} not matched".format(result["task"]))
    except Exception:
        logger.error(traceback.print_exc())
        ch.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)


def main():
    parameters = (
        pika.ConnectionParameters(host=config["RABBITMQ_HOST"], port=config["RABBITMQ_PORT"])
    )

    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.basic_qos(prefetch_count=10)
            channel.basic_consume(config["RABBITMQ_QUEUE"], on_message_callback)

            logger.info("AMQPConnection ok")
            channel.start_consuming()
        except pika.exceptions.ConnectionClosedByBroker:
            logger.info("Connection closed by broker, exit")
            break
        except pika.exceptions.AMQPChannelError:
            logger.info("AMQPChannelError, exit")
            break
        except pika.exceptions.AMQPConnectionError:
            logger.error(traceback.print_exc())
            logger.info("AMQPConectionError, try again ....")
            continue


if __name__ == "__main__":
    main()
