import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from influxdb_metrics.loader import log_metric
from rest_framework import mixins, viewsets, parsers, status, renderers, permissions
from rest_framework.response import Response
from rest_framework_json_api import renderers as jsapi_renderers, serializers

from apps.authentication import EngineRequest, get_jwt_from_request
from apps.eth.models import EthAction, Event
from apps.eth.serializers import EventSerializer, EthActionSerializer
from apps.permissions import get_owner_id
from apps.rpc_client import RPCError
from apps.shipments.permissions import IsListenerOwner

LOG = logging.getLogger('transmission')


class EventViewSet(mixins.CreateModelMixin,
                   viewsets.GenericViewSet):
    """
    Handles Event callbacks from Engine
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    parser_classes = (parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer, jsapi_renderers.JSONRenderer)
    permission_classes = (EngineRequest,)

    @staticmethod
    def _process_event(event, project):
        try:
            action = EthAction.objects.get(transaction_hash=event['transaction_hash'])
            Event.objects.get_or_create(**event, eth_action=action)
        except RPCError as exc:
            LOG.info(f"Engine RPC error processing event {event['transaction_hash']}: {exc}")
        except MultipleObjectsReturned as exc:
            LOG.info(f"MultipleObjectsReturned during get/get_or_create for event {event['transaction_hash']}: {exc}")
        except ObjectDoesNotExist:
            log_metric('transmission.info', tags={'method': 'events.create', 'code': 'non_ethaction_event',
                                                  'module': __name__, 'project': project})
            LOG.info(f"Non-EthAction Event processed Tx: {event['transaction_hash']}")

    def create(self, request, *args, **kwargs):
        log_metric('transmission.info', tags={'method': 'events.create', 'module': __name__})
        LOG.debug('Events create')

        is_many = isinstance(request.data['events'], list)
        serializer = EventSerializer(data=request.data['events'], many=is_many)
        serializer.is_valid(raise_exception=True)

        events = serializer.data if is_many else [serializer.data]

        for event in events:
            self._process_event(event, request.data['project'])

        return Response(status=status.HTTP_204_NO_CONTENT)


class TransactionViewSet(mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    """
    Get tx details for a transaction hash
    """
    queryset = EthAction.objects.all()
    serializer_class = EthActionSerializer
    permission_classes = ((IsListenerOwner, ) if settings.PROFILES_ENABLED else (permissions.AllowAny, ))

    def get_queryset(self):
        log_metric('transmission.info', tags={'method': 'transaction.get_queryset', 'module': __name__})
        LOG.debug('Getting tx details for a transaction hash.')
        queryset = self.queryset
        if settings.PROFILES_ENABLED:
            if 'wallet_id' in self.request.query_params:
                queryset = queryset.filter(Q(ethlistener__shipments__owner_id=get_owner_id(self.request)) |
                                           Q(ethlistener__shipments__shipper_wallet_id=
                                             self.request.query_params.get('wallet_id')) |
                                           Q(ethlistener__shipments__moderator_wallet_id=
                                             self.request.query_params.get('wallet_id')) |
                                           Q(ethlistener__shipments__carrier_wallet_id=
                                             self.request.query_params.get('wallet_id')))
            else:
                queryset = queryset.filter(ethlistener__shipments__owner_id=get_owner_id(self.request))

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        log_metric('transmission.info', tags={'method': 'transaction.list', 'module': __name__})

        shipment_pk = kwargs.get('shipment_pk', None)
        if shipment_pk:
            LOG.debug(f'Getting transactions for shipment: {shipment_pk}.')

            queryset = self.queryset.filter(ethlistener__shipments__id=shipment_pk)
        else:
            LOG.debug('Getting tx details filtered by wallet address.')
            if not settings.PROFILES_ENABLED:
                if 'wallet_address' not in self.request.query_params:
                    raise serializers.ValidationError(
                        'wallet_address required in query parameters')

                from_address = self.request.query_params.get('wallet_address')

            else:
                if 'wallet_id' not in self.request.query_params:
                    raise serializers.ValidationError(
                        'wallet_id required in query parameters')

                wallet_id = self.request.query_params.get('wallet_id')

                wallet_response = settings.REQUESTS_SESSION.get(
                    f'{settings.PROFILES_URL}/api/v1/wallet/{wallet_id}/?is_active',
                    headers={'Authorization': f'JWT {get_jwt_from_request(request)}'}
                )

                if not wallet_response.status_code == status.HTTP_200_OK:
                    raise serializers.ValidationError('Error retrieving Wallet from ShipChain Profiles')

                wallet_details = wallet_response.json()
                from_address = wallet_details['data']['attributes']['address']

            queryset = queryset.filter(transactionreceipt__from_address__iexact=from_address)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
