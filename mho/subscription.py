import logging
from asyncio import Queue

from onos_ric_sdk_py import E2Client
from onos_api.e2t.e2.v1beta1 import (
    Action,
    ActionType,
    SubsequentAction,
    SubsequentActionType,
    TimeToWait
)
from onos_e2_sm.e2sm_mho_go.v2 import (
    MhoTriggerType,
    E2SmMhoIndicationHeader,
    E2SmMhoIndicationMessage,
    E2SmMhoEventTriggerDefinition,
    E2SmMhoEventTriggerDefinitionFormat1,  
)

from .indication import Indication


ServiceModelName = 'oran-e2sm-mho'
ServiceModelVersion = 'v2'


def create_event_trigger(trigger_type: MhoTriggerType, period=1000) -> E2SmMhoEventTriggerDefinition:
    trigger = E2SmMhoEventTriggerDefinition()
    format1 = E2SmMhoEventTriggerDefinitionFormat1(
        trigger_type=trigger_type,
        reporting_period_ms=period,
    )
    trigger.event_definition_formats.event_definition_format1 = format1
    return trigger

async def subscribe(e2_client: E2Client, e2_node_id: str, trigger_type: MhoTriggerType, queue: Queue):
    logging.info(f'subscribe node={e2_node_id} type={trigger_type}')

    actions = [
        Action(
            id=0,
            type=ActionType.ACTION_TYPE_REPORT,
            subsequent_action=SubsequentAction(
                type=SubsequentActionType.SUBSEQUENT_ACTION_TYPE_CONTINUE,
                time_to_wait=TimeToWait.TIME_TO_WAIT_ZERO
            )
        )
    ]
    async for header_bytes, message_bytes in e2_client.subscribe(
        e2_node_id=e2_node_id,
        service_model_name=ServiceModelName,
        service_model_version=ServiceModelVersion,
        subscription_id=f'onos-mho-subscription-{e2_node_id}-{trigger_type}',
        trigger=bytes(create_event_trigger(trigger_type)),
        actions=actions
    ):
        header = E2SmMhoIndicationHeader()
        message = E2SmMhoIndicationMessage()
        header.parse(header_bytes)
        message.parse(message_bytes)

        indication = Indication(header=header, message=message)
        await queue.put(indication)

        # ue_data: Dict = dict()
        # if trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_PERIODIC:
        #     ue_data = handle_periodic_report(header, message)
        # elif trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_UPON_RCV_MEAS_REPORT:
        #     ue_data = handle_meas_report(header, message)
        # elif trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_UPON_CHANGE_RRC_STATUS:
        #     ue_data = handle_rrc_status(header, message)
        # ue_data['e2_node_id'] = e2_node_id
        # ue_data['trigger_type'] = trigger_type.name

        # logging.info(f'{ue_data}')

        # if trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_UPON_RCV_MEAS_REPORT:
        #     neighbors = sorted(
        #         message.indication_message_format1.meas_report,
        #         key=lambda report: report.rsrp.value
        #     )
        #     target_cgi = neighbors.pop().cgi

        #     control_message = E2SmMhoControlMessage(
        #         control_message_format1=E2SmMhoControlMessageFormat1(
        #             serving_cgi=header.indication_header_format1.cgi,
        #             ued_id=message.indication_message_format1.ue_id,
        #             target_cgi=neighbors.pop().cgi
        #         )
        #     )

        #     try:
        #         control_header = E2SmMhoControlHeader(
        #             control_header_format1=E2SmMhoControlHeaderFormat1(
        #                 rc_command=MhoCommand.MHO_COMMAND_INITIATE_HANDOVER,
        #                 ric_control_message_priority=RicControlMessagePriority(value=10)
        #             )
        #         )
        #         await e2_client.control(
        #             e2_node_id=e2_node_id,
        #             service_model_name=ServiceModelName,
        #             service_model_version=ServiceModelVersion,
        #             header=bytes(control_header),
        #             message=bytes(control_message)
        #         )
        #     except Exception as e:
        #         logging.error(f'control failure: {e.args}')
        #     else:      
        #         ue_id = ue_data['ue_id']
        #         serving_nci = ue_data['serving_nci']
        #         target_nci = bytes_to_string(target_cgi.n_r_cgi.n_rcell_identity.value.value)
        #         logging.info(f'control success: {ue_id} from {serving_nci} to {target_nci}')
