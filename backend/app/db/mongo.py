from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorDatabase,
    AsyncIOMotorGridFSBucket,
)

from app.core.config import setting


class MongoDataBase:
    def __init__(self, mongo_url: str, db_name: str):
        self._client = AsyncIOMotorClient(mongo_url)
        self._database = self._client[db_name]
        self._gridfs_bucket = AsyncIOMotorGridFSBucket(
            self._database,
            bucket_name=setting.image_bucket_name,
        )

    @property
    def database(self) -> AsyncIOMotorDatabase:
        return self._database

    @property
    def gridfs_bucket(self) -> AsyncIOMotorGridFSBucket:
        return self._gridfs_bucket

    def close(self) -> None:
        self._client.close()


db_mongo = MongoDataBase(
    mongo_url=setting.mongodb_url,
    db_name=setting.mongodb_db_name,
)
