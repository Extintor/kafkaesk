from kafkaesk.utils import run_async
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import kafka
import kafka.admin
import kafka.admin.client


class KafkaTopicManager:
    _admin_client: Optional[kafka.admin.client.KafkaAdminClient]
    _client: Optional[kafka.KafkaClient]

    def __init__(self, bootstrap_servers: List[str], prefix: str = ""):
        self.prefix = prefix
        self._bootstrap_servers = bootstrap_servers
        self._admin_client = self._client = None

    async def finalize(self) -> None:
        if self._admin_client is not None:
            await run_async(self._admin_client.close)
            self._admin_client = None
        if self._client is not None:
            await run_async(self._client.close)
            self._client = None

    def get_topic_id(self, topic: str) -> str:
        return f"{self.prefix}{topic}"

    def get_schema_topic_id(self, schema_name: str) -> str:
        return f"{self.prefix}__schema__{schema_name}"

    async def get_admin_client(self) -> kafka.admin.client.KafkaAdminClient:
        if self._admin_client is None:
            self._admin_client = await run_async(
                kafka.admin.client.KafkaAdminClient, bootstrap_servers=self._bootstrap_servers
            )
        return self._admin_client

    async def topic_exists(self, topic: str) -> bool:
        if self._client is None:
            self._client = await run_async(kafka.KafkaClient, self._bootstrap_servers)
        return topic in self._client.topic_partitions

    async def create_topic(
        self,
        topic: str,
        *,
        partitions: int = 7,
        replicas: int = 1,
        retention_ms: Optional[int] = None,
        cleanup_policy: Optional[str] = None,
    ) -> None:
        topic_configs: Dict[str, Any] = {}
        if retention_ms is not None:
            topic_configs["retention.ms"] = retention_ms
        if cleanup_policy is not None:
            topic_configs["cleanup.policy"] = cleanup_policy
        new_topic = kafka.admin.NewTopic(topic, partitions, replicas, topic_configs=topic_configs)
        client = await self.get_admin_client()
        await run_async(client.create_topics, [new_topic])
        if self._client is not None:
            self._client.topic_partitions[topic] = [i for i in range(partitions)]
        return None
