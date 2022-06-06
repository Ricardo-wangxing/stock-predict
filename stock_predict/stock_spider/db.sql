create schema if not exists stock_infos ;
use stock_info;
create table `all_securities`(
    `id` int auto_increment primary key ,
    `code` varchar(11) default null comment '股票代码',
    `name` varchar(10) default null comment '股票名字',
    `start_date` date default null comment  '上市日期',
    `end_date` date default null comment '退市日期'
)comment '沪深股票基本信息';
create table `hs300_stock_price_pool`(
    `id` int auto_increment primary key ,
    `code` varchar(11) default null comment '股票代码',
    `name` varchar(10) default null comment '股票名字',
    `date` date comment '日期',
    `open` float default null comment '开盘价',
    `close` float comment '收盘价',
    `high` float comment '最高价',
    `low` float comment '最低价'
);
create table hs300_details(
    id int auto_increment primary key ,
    code varchar(11) comment '股票代码',
    name varchar(10) comment '股票名字',
    date date comment '上市时间',
    is_exist bool comment '是否属于成分股'
);
create table stock_price_pool(
    `id` int auto_increment primary key ,
    `code` varchar(11) default null comment '股票代码',
    `name` varchar(10) default null comment '股票名字',
    `date` date comment '日期',
    `open` float default null comment '开盘价',
    `close` float comment '收盘价',
    `high` float comment '最高价',
    `low` float comment '最低价',
    `volume` bigint comment '成交量',
    `money` bigint comment '成交额'
);