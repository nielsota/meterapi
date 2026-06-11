"""Shared OpenAPI `responses` maps for routers."""
from meterapi.models.api import ErrorResponse, ValidationErrorResponse

NOT_FOUND = {404: {"model": ErrorResponse}}
BAD_REQUEST = {400: {"model": ErrorResponse}}
SERVICE_UNAVAILABLE = {503: {"model": ErrorResponse}}
VALIDATION_ERROR = {422: {"model": ValidationErrorResponse}}
