from collections import OrderedDict

import json
import copy
import boto3
from dateutil.parser import parse
from botocore.exceptions import ClientError
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.conf import settings
from django.db import transaction
from enumfields.drf import EnumField
from enumfields.drf.serializers import EnumSupportSerializerMixin
from jose import jws, JWSError
from rest_framework import exceptions
from rest_framework import status
from rest_framework import serializers as rest_serializers
from rest_framework.utils import model_meta
from rest_framework.fields import SkipField
from rest_framework_json_api import serializers


from apps.shipments.models import Shipment, Device, Location, LoadShipment, FundingType, EscrowState, ShipmentState, \
    TrackingData


class NullableFieldsMixin:
    def to_representation(self, instance):
        # Remove null fields from serialized object
        ret = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            if attribute is not None:
                representation = field.to_representation(attribute)
                if representation is None:
                    # Do not serialize empty objects
                    continue
                if isinstance(representation, list) and not representation:
                    # Do not serialize empty lists
                    continue
                ret[field.field_name] = representation

        return ret


class DeviceSerializer(NullableFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class LocationSerializer(NullableFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for a location, used nested in a Shipment
    """

    class Meta:
        model = Location
        fields = '__all__'
        read_only_fields = ('owner_id',) if settings.PROFILES_ENABLED else ()


class LocationVaultSerializer(NullableFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for a location, used nested in a Shipment
    """

    class Meta:
        model = Location
        exclude = ('owner_id', 'geometry')


class LoadShipmentSerializer(NullableFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for a location, used nested in a Shipment
    """
    funding_type = EnumField(FundingType, ints_as_names=True)
    escrow_state = EnumField(EscrowState, ints_as_names=True)
    shipment_state = EnumField(ShipmentState, ints_as_names=True)

    class Meta:
        model = LoadShipment
        fields = '__all__'


class ShipmentSerializer(serializers.ModelSerializer, EnumSupportSerializerMixin):
    """
    Serializer for a shipment object
    """
    load_data = LoadShipmentSerializer(source='loadshipment', required=False)
    ship_from_location = LocationSerializer(required=False)
    ship_to_location = LocationSerializer(required=False)
    device = DeviceSerializer(required=False)

    transactions = serializers.SerializerMethodField()

    def get_transactions(self, obj):
        return [eth_action.transaction_hash for eth_action in obj.ethaction_set.all()]

    class Meta:
        model = Shipment
        fields = '__all__'
        read_only_fields = ('owner_id', 'contract_version') if settings.PROFILES_ENABLED else ('contract_version',)

    class JSONAPIMeta:
        included_resources = ['ship_from_location', 'ship_to_location',
                              'final_destination_location', 'load_data', 'device']


class ShipmentCreateSerializer(ShipmentSerializer):
    device_id = serializers.CharField(max_length=36, required=False)

    def create(self, validated_data):
        extra_args = {}

        auth = self.context['auth']

        with transaction.atomic():
            for location_field in ['ship_from_location', 'ship_to_location']:
                if location_field in validated_data:
                    data = validated_data.pop(location_field)
                    if 'owner_id' not in data:
                        data['owner_id'] = validated_data['owner_id']
                    extra_args[location_field], _ = Location.objects.get_or_create(**data)

            if 'device_id' in validated_data:
                extra_args['device'] = Device.get_or_create_with_permission(auth, validated_data.pop('device_id'))

            return Shipment.objects.create(**validated_data, **extra_args)

    def validate_shipper_wallet_id(self, shipper_wallet_id):
        if settings.PROFILES_ENABLED:
            auth = self.context['auth']
            response = settings.REQUESTS_SESSION.get(f'{settings.PROFILES_URL}/api/v1/wallet/{shipper_wallet_id}/',
                                                     headers={'Authorization': 'JWT {}'.format(auth.decode())})

            if response.status_code != status.HTTP_200_OK:
                raise serializers.ValidationError('User does not have access to this wallet in ShipChain Profiles')

        return shipper_wallet_id

    def validate_storage_credentials_id(self, storage_credentials_id):
        if settings.PROFILES_ENABLED:
            auth = self.context['auth']
            response = settings.REQUESTS_SESSION.get(
                f'{settings.PROFILES_URL}/api/v1/storage_credentials/{storage_credentials_id}/',
                headers={'Authorization': 'JWT {}'.format(auth.decode())})

            if response.status_code != status.HTTP_200_OK:
                raise serializers.ValidationError(
                    'User does not have access to this storage credential in ShipChain Profiles')

        return storage_credentials_id


class ShipmentUpdateSerializer(ShipmentSerializer):
    device_id = serializers.CharField(max_length=36)

    class Meta:
        model = Shipment
        fields = '__all__'
        if settings.PROFILES_ENABLED:
            read_only_fields = ('owner_id', 'vault_id', 'vault_uri', 'shipper_wallet_id', 'carrier_wallet_id',
                                'storage_credentials_id', 'contract_version')
        else:
            read_only_fields = ('vault_id', 'vault_uri', 'shipper_wallet_id', 'carrier_wallet_id',
                                'storage_credentials_id', 'contract_version')

    def update(self, instance, validated_data):
        auth = self.context['auth']

        if 'device_id' in validated_data:
            instance.device = Device.get_or_create_with_permission(auth, validated_data.pop('device_id'))

        for location_field in ['ship_from_location', 'ship_to_location']:
            if location_field in validated_data:
                location = getattr(instance, location_field)
                data = validated_data.pop(location_field)

                if location:
                    for attr, value in data.items():
                        setattr(location, attr, value)
                    location.save()

                else:
                    location, _ = Location.objects.get_or_create(**data)
                    setattr(instance, location_field, location)

        info = model_meta.get_field_info(instance)
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                field = getattr(instance, attr)
                field.set(value)
            else:
                setattr(instance, attr, value)

        instance.save()
        return instance


class ShipmentTxSerializer(serializers.ModelSerializer):
    async_job_id = serializers.CharField(max_length=36)

    load_data = LoadShipmentSerializer(source='loadshipment', required=False)
    ship_from_location = LocationSerializer(required=False)
    ship_to_location = LocationSerializer(required=False)
    device = DeviceSerializer(required=False)

    class Meta:
        model = Shipment
        fields = '__all__'
        read_only_fields = ('owner_id',)
        meta_fields = ('async_job_id',)

    class JSONAPIMeta:
        included_resources = ['ship_from_location', 'ship_to_location',
                              'final_destination_location', 'load_data', 'device']


class ShipmentVaultSerializer(NullableFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for a shipment vault object
    """

    ship_from_location = LocationVaultSerializer(required=False)
    ship_to_location = LocationVaultSerializer(required=False)

    class Meta:
        model = Shipment
        exclude = ('owner_id', 'storage_credentials_id',
                   'vault_id', 'vault_uri', 'shipper_wallet_id', 'carrier_wallet_id',
                   'contract_version', 'device')


class TrackingDataSerializer(serializers.Serializer):
    payload = serializers.RegexField(r'^[a-zA-Z0-9\-_]+?\.[a-zA-Z0-9\-_]+?\.([a-zA-Z0-9\-_]+)?$')

    def validate(self, attrs):
        payload = attrs['payload']
        shipment = self.context['shipment']
        try:
            header = jws.get_unverified_header(payload)
        except JWSError as exc:
            raise exceptions.ValidationError(f"Invalid JWS: {exc}")

        # Ensure that the device is allowed to update the Shipment tracking data
        if not shipment.device:
            raise exceptions.PermissionDenied(f"No device for shipment {shipment.id}")
        elif header['kid'] != shipment.device.certificate_id:
            raise exceptions.PermissionDenied(f"Certificate {header['kid']} is "
                                              f"not associated with shipment {shipment.id}")

        try:
            # Look up JWK for device from AWS IoT
            iot = boto3.client('iot', region_name='us-east-1')
            cert = iot.describe_certificate(certificateId=header['kid'])

            if cert['certificateDescription']['status'] == 'ACTIVE':
                # Get public key PEM from x509 cert
                certificate = cert['certificateDescription']['certificatePem'].encode()
                public_key = x509.load_pem_x509_certificate(certificate, default_backend()).public_key().public_bytes(
                    encoding=Encoding.PEM, format=PublicFormat.SubjectPublicKeyInfo).decode()

                # Validate authenticity and integrity of message signature
                attrs['payload'] = json.loads(jws.verify(payload, public_key, header['alg']).decode("utf-8"))
            else:
                raise exceptions.PermissionDenied(f"Certificate {header['kid']} is "
                                                  f"not ACTIVE in IoT for shipment {shipment.id}")
        except ClientError as exc:
            raise exceptions.APIException(f'boto3 error when validating tracking update: {exc}')
        except JWSError as exc:
            raise exceptions.PermissionDenied(f'Error validating tracking data JWS: {exc}')

        return attrs


class UnvalidatedTrackingDataSerializer(serializers.Serializer):
    payload = serializers.JSONField()

    def validate(self, attrs):
        shipment = self.context['shipment']

        # Ensure that the device is allowed to update the Shipment tracking data
        if not shipment.device:
            raise exceptions.PermissionDenied(f"No device for shipment {shipment.id}")

        return attrs


class TrackingDataToDbSerializer(rest_serializers.ModelSerializer):
    """
    Serializer for tracking data to be cached in db
    """
    def __init__(self, *args, **kwargs):
        raw_data = copy.deepcopy(kwargs['data'])
        data = {}
        data.update(raw_data['position'])
        raw_data.pop('position')
        data.update(raw_data)

        # Ensure that the timestamps is valid
        try:
            data['timestamp'] = parse(data['timestamp'])
        except Exception as exception:
            raise exceptions.ValidationError(detail=f"Unable to parse tracking data timestamp in to datetime object: \
                                                    {exception}")

        kwargs.pop('data')
        kwargs['data'] = data
        super().__init__(*args, **kwargs)

    shipment = ShipmentSerializer(read_only=True)

    class Meta:
        model = TrackingData
        fields = '__all__'

    # def validate(self, attrs):
    #     instance = TrackingData(**attrs)
    #     instance.clean()
    #     return attrs

    def create(self, validated_data):
        data = TrackingData.objects.create(**validated_data, shipment=self.context['shipment'])
        data.save()

        return data
