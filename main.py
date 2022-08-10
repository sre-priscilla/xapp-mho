import os
import asyncio
import logging
from asyncio import Queue
from typing import Callable
from argparse import ArgumentParser, Namespace

import onos_ric_sdk_py as ricsdk
from onos_ric_sdk_py import E2Client, SDLClient
from onos_e2_sm.e2sm_mho_go.v2 import MhoTriggerType

from rl.env import State, Env
from mho.subscription import subscribe, Indication



ServiceModelName = 'oran-e2sm-mho'
ServiceModelVersion = 'v2'
MhoTriggerTypes = (
    MhoTriggerType.MHO_TRIGGER_TYPE_PERIODIC,
    MhoTriggerType.MHO_TRIGGER_TYPE_UPON_RCV_MEAS_REPORT,
    MhoTriggerType.MHO_TRIGGER_TYPE_UPON_CHANGE_RRC_STATUS,
)


async def init_subscriptions(e2_client: E2Client, e2_node_id: str, queue: Queue):
    subscriptions = [
        subscribe(e2_client, e2_node_id, trigger_type, queue)
        for trigger_type in MhoTriggerTypes
    ]
    await asyncio.gather(*subscriptions)

async def process_indications(queue: Queue, handler: Callable[[Indication]]):
    while True:
        indication: Indication = await queue.get()
        handler(indication)


async def async_main(e2_client: E2Client, sdl_client: SDLClient, max_cells: int, max_ues: int):
    queue = asyncio.Queue()
    environment = Env(prev=None, curr=State(max_cells, max_ues))

    async with e2_client, sdl_client:
        asyncio.create_task(process_indications(queue))
        async for e2_node_id, _ in sdl_client.watch_e2_connections():
            logging.info(f'{e2_node_id}')
            asyncio.create_task(init_subscriptions(e2_client, e2_node_id, queue))   
    


if __name__ == '__main__':
    parser = ArgumentParser(description='xapp-mho')
    parser.add_argument('--log_level', type=str, default='INFO', help='log level')
    parser.add_argument('--app_id', type=str, default='xapp-mho', help='app ID')
    parser.add_argument('--topo_endpoint', type=str, default='onos-topo:5150', help='topo endpoint')
    parser.add_argument('--max-cells', type=int, default=6, help='max cells')
    parser.add_argument('--max-ues', type=int, default=10, help='max ues')
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
    ricsdk.run(async_main(e2_client, sdl_client, args.max_cells, args.max_ues), os.getcwd())
