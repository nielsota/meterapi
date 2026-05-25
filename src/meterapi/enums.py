from enum import StrEnum

class MeterCommunicationProtocol(StrEnum):
    LORA = 'lora'
    WMBUS = 'wmBus'