from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from stock_predict.stock_spider.config import config
from job import run_today
import jqdatasdk as jq
import time

sched=BlockingScheduler()


def trade_day_run():
    today_str = time.strftime("%Y-%m-%d",time.localtime())
    jq.auth(config["jqdata_user"],config["jqdata_password"])
    df = jq.get_trade_days(today_str,today_str)
    if df == []:
        pass
    else:
        run_today()

if __name__ == '__main__':
    scheduler = BlockingScheduler()
    scheduler.add_job(trade_day_run, 'cron', hour=19,minute=6)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
