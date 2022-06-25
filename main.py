import os
import asyncio
import logging
from typing import AnyStr, Dict, List
from argparse import ArgumentParser, Namespace

import onos_ric_sdk_py as ricsdk
from onos_ric_sdk_py import E2Client, SDLClient
from onos_api.e2t.e2.v1beta1 import (
    Action,
    ActionType,
    SubsequentAction,
    SubsequentActionType,
    TimeToWait
)
from onos_e2_sm.e2sm_mho_go.v2 import (
    E2SmMhoControlHeader,
    E2SmMhoControlHeaderFormat1,
    E2SmMhoControlMessage,
    E2SmMhoControlMessageFormat1,
    E2SmMhoEventTriggerDefinition,
    E2SmMhoEventTriggerDefinitionFormat1,
    E2SmMhoIndicationHeader,
    E2SmMhoIndicationMessage,
    E2SmMhoMeasurementReportItem,
    MhoCommand,
    MhoTriggerType,
    RicControlMessagePriority,
)


ServiceModelName = 'oran-e2sm-mho'
ServiceModelVersion = 'v2'
MhoTriggerTypes = [
    # MhoTriggerType.MHO_TRIGGER_TYPE_PERIODIC,
    MhoTriggerType.MHO_TRIGGER_TYPE_UPON_RCV_MEAS_REPORT,
    MhoTriggerType.MHO_TRIGGER_TYPE_UPON_CHANGE_RRC_STATUS,
]
ActionReport = Action(
    id=0,
    type=ActionType.ACTION_TYPE_REPORT,
    subsequent_action=SubsequentAction(
        type=SubsequentActionType.SUBSEQUENT_ACTION_TYPE_CONTINUE,
        time_to_wait=TimeToWait.TIME_TO_WAIT_ZERO
    )
)
ControlHeader = E2SmMhoControlHeader(
    control_header_format1=E2SmMhoControlHeaderFormat1(
        rc_command=MhoCommand.MHO_COMMAND_INITIATE_HANDOVER,
        ric_control_message_priority=RicControlMessagePriority(value=10)
    )
)


def bytes_to_string(bs: AnyStr) -> AnyStr:
    return ''.join([f'{ch}' for ch in bs])


def create_event_trigger(trigger_type: MhoTriggerType, period=1000) -> E2SmMhoEventTriggerDefinition:
    trigger = E2SmMhoEventTriggerDefinition()
    format1 = E2SmMhoEventTriggerDefinitionFormat1(
        trigger_type=trigger_type,
        reporting_period_ms=period,
    )
    trigger.event_definition_formats.event_definition_format1 = format1
    return trigger


def handle_periodic_report(header: E2SmMhoControlHeader, message: E2SmMhoIndicationMessage) -> Dict:
    serving_nci: bytes = header.indication_header_format1.cgi.n_r_cgi.n_rcell_identity.value.value
    meas_reports: List[E2SmMhoMeasurementReportItem] = message.indication_message_format1.meas_report

    return dict(
        ue_id=message.indication_message_format1.ue_id.g_nb_ueid.amf_ue_ngap_id.value,
        serving_nci=bytes_to_string(serving_nci),
        neighbors={
            bytes_to_string(meas_report.cgi.n_r_cgi.n_rcell_identity.value.value): meas_report.rsrp.value
            for meas_report in meas_reports
        }
    )


def handle_meas_report(header: E2SmMhoControlHeader, message: E2SmMhoIndicationMessage) -> Dict:
    serving_nci: bytes = header.indication_header_format1.cgi.n_r_cgi.n_rcell_identity.value.value
    meas_reports: List[E2SmMhoMeasurementReportItem] = message.indication_message_format1.meas_report

    five_qi_values = [
        meas_report.five_qi.value
        for meas_report in meas_reports
        if (meas_report.five_qi and meas_report.five_qi.value > -1)
    ]

    return dict(
        ue_id=message.indication_message_format1.ue_id.g_nb_ueid.amf_ue_ngap_id.value,
        serving_nci=bytes_to_string(serving_nci),
        neighbors={
            bytes_to_string(meas_report.cgi.n_r_cgi.n_rcell_identity.value.value): meas_report.rsrp.value
            for meas_report in meas_reports
        },
        five_qi=(0 if len(five_qi_values) == 0 else five_qi_values[0])
    )


def handle_rrc_status(header: E2SmMhoControlHeader, message: E2SmMhoIndicationMessage) -> Dict:
    serving_nci: bytes = header.indication_header_format1.cgi.n_r_cgi.n_rcell_identity.value.value

    return dict(
        ue_id=message.indication_message_format2.ue_id.g_nb_ueid.amf_ue_ngap_id.value,
        serving_nci=bytes_to_string(serving_nci),
        rrc_status=message.indication_message_format2.rrc_status
    )


async def subscribe(e2_client: E2Client, e2_node_id: str, trigger_type: MhoTriggerType):
    logging.info(f'subscription node={e2_node_id} type={trigger_type}')
    async for header_bytes, message_bytes in e2_client.subscribe(
        e2_node_id=e2_node_id,
        service_model_name=ServiceModelName,
        service_model_version=ServiceModelVersion,
        subscription_id=f'onos-mho-subscription-{e2_node_id}-{trigger_type}',
        trigger=bytes(create_event_trigger(trigger_type)),
        actions=[ActionReport]
    ):
        header = E2SmMhoIndicationHeader()
        message = E2SmMhoIndicationMessage()
        header.parse(header_bytes)
        message.parse(message_bytes)

        ue_data: Dict = dict()
        if trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_PERIODIC:
            ue_data = handle_periodic_report(header, message)
        elif trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_UPON_RCV_MEAS_REPORT:
            ue_data = handle_meas_report(header, message)
        elif trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_UPON_CHANGE_RRC_STATUS:
            ue_data = handle_rrc_status(header, message)
        ue_data['e2_node_id'] = e2_node_id
        ue_data['trigger_type'] = trigger_type.name

        logging.info(f'{ue_data}')

        def report_rsrp(report: E2SmMhoMeasurementReportItem) -> int:
            return report.rsrp.value

        if trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_UPON_RCV_MEAS_REPORT:
            neighbors = sorted(
                message.indication_message_format1.meas_report,
                key=report_rsrp
            )
            target_cgi = neighbors.pop().cgi

            control_message = E2SmMhoControlMessage(
                control_message_format1=E2SmMhoControlMessageFormat1(
                    serving_cgi=header.indication_header_format1.cgi,
                    ued_id=message.indication_message_format1.ue_id,
                    target_cgi=neighbors.pop().cgi
                )
            )

            try:
                await e2_client.control(
                    e2_node_id=e2_node_id,
                    service_model_name=ServiceModelName,
                    service_model_version=ServiceModelVersion,
                    header=bytes(ControlHeader),
                    message=bytes(control_message)
                )
            except Exception as e:
                logging.error(f'control failure: {e.args}')
            
            ue_id = ue_data['ue_id']
            serving_nci = ue_data['serving_nci']
            target_nci = bytes_to_string(target_cgi.n_r_cgi.n_rcell_identity.value.value)
            logging.info(f'control success: {ue_id} from {serving_nci} to {target_nci}')


async def run(e2_client: E2Client, e2_node_id: str):
    subscriptions = [
        subscribe(e2_client, e2_node_id, trigger_type)
        for trigger_type in MhoTriggerTypes
    ]
    await asyncio.gather(*subscriptions)


async def async_main(e2_client: E2Client, sdl_client: SDLClient):
    async with e2_client, sdl_client:
        async for e2_node_id, _ in sdl_client.watch_e2_connections():
            logging.info(f'{e2_node_id}')
            asyncio.create_task(run(e2_client, e2_node_id))


if __name__ == '__main__':
    parser = ArgumentParser(description='xapp-mho')
    parser.add_argument('--log_level', type=str, default='INFO', help='log level')
    parser.add_argument('--app_id', type=str, default='xapp-mho', help='app ID')
    parser.add_argument('--topo_endpoint', type=str, default='onos-topo:5150', help='topo endpoint')
    parser.add_argument('--ca_path', type=str, default='/etc/xapp-mho/pki/ca.crt', help='ca')
    parser.add_argument('--cert_path', type=str, default='/etc/xapp-mho/pki/tls.crt', help='tls crt')
    parser.add_argument('--key_path', type=str, default='/etc/xapp-mho/pki/tls.key', help='tls key')
    args: Namespace = parser.parse_args()

    e2_client = E2Client(
        app_id=args.app_id,
        e2t_endpoint='onos-e2t:5150',
        ca_path=args.ca_path,
        cert_path=args.cert_path,
        key_path=args.key_path
    )
    sdl_client = SDLClient(
        topo_endpoint=args.topo_endpoint,
        ca_path=args.ca_path,
        cert_path=args.cert_path,
        key_path=args.key_path
    )
    ricsdk.run(async_main(e2_client, sdl_client), os.getcwd())
