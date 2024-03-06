import datetime
import logging

import aioboto3
from pydantic import BaseModel

logger = logging.getLogger(__name__)
session = aioboto3.Session()


class BaseTable(BaseModel):

    def to_table_item(self):
        return to_table_item(dict(self))

    @classmethod
    def from_table_item(cls, d):
        result = {}
        for k, v in d.items():
            assert len(v) == 1
            _type, value = list(v.items())[0]

            if _type == "N":
                result[k] = float(value)
            elif _type == "NS":
                result[k] = [float(i) for i in value]
            elif _type == "L":
                result[k] = [cls.from_table_item(i) for i in value]
            elif _type == "M":
                result[k] = cls.from_table_item(value)
            elif _type == "NULL":
                result[k] = None
            else:
                result[k] = value

        return cls(**result)


def to_table_item(d: dict):
    result = {}
    for k, v in d.items():
        if type(v) is str:
            result[k] = {"S": v}
        elif type(v) is int or type(v) is float:
            result[k] = {"N": str(v)}
        elif type(v) is bool:
            result[k] = {"BOOL": v}
        elif type(v) is bytes:
            result[k] = {"B": v}
        elif type(v) is list:
            if all((type(i) is str for i in v)):
                result[k] = {"SS": v}
            elif all((type(i) is int or type(i) is float for i in v)):
                result[k] = {"NS": [str(i) for i in v]}
            elif all((type(i) is bytes for i in v)):
                result[k] = {"BS": v}
            elif all((type(i) is dict for i in v)):
                result[k] = {"L": [to_table_item(i) for i in v]}
            elif all((isinstance(i, BaseTable) for i in v)):
                result[k] = {"L": [i.to_table_item() for i in v]}
        elif type(v) is dict:
            result[k] = {"M": to_table_item(v)}
        elif isinstance(v, BaseTable):
            result[k] = {"M": v.to_table_item()}
        elif v is None:
            result[k] = {"NULL": True}
        elif isinstance(v, datetime.datetime):
            result[k] = {"S": v.isoformat()}
        else:
            raise Exception(f"unsupported type '{type(v)}' for key '{k}'")

    return result


async def scan_all(**kwargs):
    params = {}
    async with session.client("dynamodb") as dynamo_db:
        while True:
            result = await dynamo_db.scan(Limit=100, **kwargs, **params)
            for item in result['Items']:
                yield item

            if "LastEvaluatedKey" not in result or result["LastEvaluatedKey"] == {}:
                break
            params["ExclusiveStartKey"] = result["LastEvaluatedKey"]
