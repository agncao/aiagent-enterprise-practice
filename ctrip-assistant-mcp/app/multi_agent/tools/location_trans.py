
def transform_location(chinese_city):
    city_dict = {
        '北京': 'Beijing',
        '上海': 'Shanghai',
        '广州': 'Guangzhou',
        '深圳': 'Shenzhen',
        '成都': 'Chengdu',
        '杭州': 'Hangzhou',
        '巴塞尔': 'Basel',
        '苏黎世': 'Zurich',
    }

    if chinese_city is None:
        return None
    if not isinstance(chinese_city, str):
        return chinese_city
    if all('\u4e00' <= char <= '\u9fff' for char in chinese_city):
        return city_dict.get(chinese_city, chinese_city)
    return chinese_city