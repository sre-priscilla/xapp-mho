import re
from typing import Dict
from dataclasses import dataclass

from onos_e2_sm.e2sm_mho_go.v2 import (
    Cgi,
    Ueid,
    MhoTriggerType,
    E2SmMhoIndicationHeader,
    E2SmMhoIndicationMessage
)


@dataclass
class Indication:
    trigger_type: MhoTriggerType
    header: E2SmMhoIndicationHeader
    message: E2SmMhoIndicationMessage

    @property
    def ue_id(self) -> Ueid:
        if self.trigger_type == MhoTriggerType.MHO_TRIGGER_TYPE_UPON_CHANGE_RRC_STATUS:
            return self.message.indication_message_format2.ue_id
        else:
            return self.message.indication_message_format1.ue_id
        

    @property
    def serving_cell_id(self) -> Cgi:
        return self.header.indication_header_format1.cgi.n_r_cgi.n_rcell_identity.value

    @property
    def neighbors(self) -> Dict[Cgi, int]:
        return {
            meas_report.cgi: meas_report.rsrp.value
            for meas_report in self.message.indication_message_format1.meas_report
        }


# def handle_periodic_report(header: E2SmMhoControlHeader, message: E2SmMhoIndicationMessage) -> Dict:
#     serving_nci: bytes = header.indication_header_format1.cgi.n_r_cgi.n_rcell_identity.value.value
#     meas_reports: List[E2SmMhoMeasurementReportItem] = message.indication_message_format1.meas_report

#     return dict(
#         ue_id=message.indication_message_format1.ue_id.g_nb_ueid.amf_ue_ngap_id.value,
#         serving_nci=bytes_to_string(serving_nci),
#         neighbors={
#             bytes_to_string(meas_report.cgi.n_r_cgi.n_rcell_identity.value.value): meas_report.rsrp.value
#             for meas_report in meas_reports
#         }
#     )

# def handle_meas_report(header: E2SmMhoControlHeader, message: E2SmMhoIndicationMessage) -> Dict:
#     serving_nci: bytes = header.indication_header_format1.cgi.n_r_cgi.n_rcell_identity.value.value
#     meas_reports: List[E2SmMhoMeasurementReportItem] = message.indication_message_format1.meas_report

#     five_qi_values = [
#         meas_report.five_qi.value
#         for meas_report in meas_reports
#         if (meas_report.five_qi and meas_report.five_qi.value > -1)
#     ]

#     return dict(
#         ue_id=message.indication_message_format1.ue_id.g_nb_ueid.amf_ue_ngap_id.value,
#         serving_nci=bytes_to_string(serving_nci),
#         neighbors={
#             bytes_to_string(meas_report.cgi.n_r_cgi.n_rcell_identity.value.value): meas_report.rsrp.value
#             for meas_report in meas_reports
#         },
#         five_qi=(0 if len(five_qi_values) == 0 else five_qi_values[0])
#     )


# def handle_rrc_status(header: E2SmMhoControlHeader, message: E2SmMhoIndicationMessage) -> Dict:
#     serving_nci: bytes = header.indication_header_format1.cgi.n_r_cgi.n_rcell_identity.value.value

#     return dict(
#         ue_id=message.indication_message_format2.ue_id.g_nb_ueid.amf_ue_ngap_id.value,
#         serving_nci=bytes_to_string(serving_nci),
#         rrc_status=message.indication_message_format2.rrc_status
#     )