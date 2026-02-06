from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from db import configure_db


# 1. Загружаем конфиг, чтобы достать user/password отдельно
db_config = configure_db()

# 2. Инициализируем Spark
spark = SparkSession.builder \
    .appName("PropertyAnalytics") \
    .config("spark.jars.packages", "org.postgresql:postgresql:42.7.2") \
    .getOrCreate()

# Формируем JDBC URL
jdbc_url = f"jdbc:postgresql://{db_config['host']}:{db_config['port']}/{db_config['db']}"

# Параметры для записи/чтения
jdbc_properties = {
    "user": db_config['user'],
    "password": db_config['password'],
    "driver": "org.postgresql.Driver"
}

# 3. Читаем данные из созданной Scrapy таблицы
df = spark.read.jdbc(url=jdbc_url, table="properties", properties=jdbc_properties)


# 4. Пример аналитики: средняя цена по типу недвижимости
analytics_df = df.filter((F.col("price_usd") > 0) & (F.col("area") > 0)) \
    .groupBy("country", "property_type") \
    .agg(
        F.count("*").alias("count"),
        F.round(F.avg("price_usd"), 0).alias("avg_total_price"),
        F.round(F.avg(F.col("price_usd") / F.col("area")), 2).alias("avg_sqm_price"),
        F.round(F.min("price_usd"), 2).alias("min_price_unit"),
        F.round(F.max("price_usd"), 2).alias("max_price_unit")
    ) \
    .orderBy(F.desc("country"), F.desc("property_type"))

# 5. Выводим результат в терминал
analytics_df.show()

# 6. Сохраняем результат в отдельную таблицу-витрину
analytics_df.write \
    .mode("overwrite") \
    .jdbc(url=jdbc_url, table="property_analytics_summary", properties=jdbc_properties)

print("Данные успешно проанализированы и сохранены!")