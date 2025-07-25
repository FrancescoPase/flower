# Copyright 2025 Flower Labs GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Main loop for Flower SuperNode."""


import os
import subprocess
import time
from collections.abc import Iterator
from contextlib import contextmanager
from logging import INFO, WARN
from pathlib import Path
from typing import Callable, Optional, Union

import grpc
from cryptography.hazmat.primitives.asymmetric import ec
from grpc import RpcError

from flwr.client.grpc_adapter_client.connection import grpc_adapter
from flwr.client.grpc_rere_client.connection import grpc_request_response
from flwr.common import GRPC_MAX_MESSAGE_LENGTH, Context, Message, RecordDict
from flwr.common.address import parse_address
from flwr.common.config import get_flwr_dir, get_fused_config_from_fab
from flwr.common.constant import (
    CLIENT_OCTET,
    CLIENTAPPIO_API_DEFAULT_SERVER_ADDRESS,
    ISOLATION_MODE_SUBPROCESS,
    MAX_RETRY_DELAY,
    SERVER_OCTET,
    TRANSPORT_TYPE_GRPC_ADAPTER,
    TRANSPORT_TYPE_GRPC_RERE,
    TRANSPORT_TYPE_REST,
    TRANSPORT_TYPES,
)
from flwr.common.exit import ExitCode, flwr_exit
from flwr.common.exit_handlers import register_exit_handlers
from flwr.common.grpc import generic_create_grpc_server
from flwr.common.inflatable import (
    get_all_nested_objects,
    get_object_tree,
    no_object_id_recompute,
)
from flwr.common.logger import log
from flwr.common.retry_invoker import RetryInvoker, RetryState, exponential
from flwr.common.telemetry import EventType
from flwr.common.typing import Fab, Run, RunNotRunningException, UserConfig
from flwr.proto.clientappio_pb2_grpc import add_ClientAppIoServicer_to_server
from flwr.supercore.ffs import Ffs, FfsFactory
from flwr.supercore.object_store import ObjectStore, ObjectStoreFactory
from flwr.supernode.nodestate import NodeState, NodeStateFactory
from flwr.supernode.servicer.clientappio import ClientAppIoServicer

DEFAULT_FFS_DIR = get_flwr_dir() / "supernode" / "ffs"


# pylint: disable=import-outside-toplevel
# pylint: disable=too-many-branches
# pylint: disable=too-many-locals
# pylint: disable=too-many-statements
# pylint: disable=too-many-arguments
def start_client_internal(
    *,
    server_address: str,
    node_config: UserConfig,
    root_certificates: Optional[Union[bytes, str]] = None,
    insecure: Optional[bool] = None,
    transport: str,
    authentication_keys: Optional[
        tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]
    ] = None,
    max_retries: Optional[int] = None,
    max_wait_time: Optional[float] = None,
    flwr_path: Optional[Path] = None,
    isolation: str = ISOLATION_MODE_SUBPROCESS,
    clientappio_api_address: str = CLIENTAPPIO_API_DEFAULT_SERVER_ADDRESS,
) -> None:
    """Start a Flower client node which connects to a Flower server.

    Parameters
    ----------
    server_address : str
        The IPv4 or IPv6 address of the server. If the Flower
        server runs on the same machine on port 8080, then `server_address`
        would be `"[::]:8080"`.
    node_config: UserConfig
        The configuration of the node.
    root_certificates : Optional[Union[bytes, str]] (default: None)
        The PEM-encoded root certificates as a byte string or a path string.
        If provided, a secure connection using the certificates will be
        established to an SSL-enabled Flower server.
    insecure : Optional[bool] (default: None)
        Starts an insecure gRPC connection when True. Enables HTTPS connection
        when False, using system certificates if `root_certificates` is None.
    transport : str
        Configure the transport layer. Allowed values:
        - 'grpc-rere': gRPC, request-response
        - 'grpc-adapter': gRPC via 3rd party adapter (experimental)
        - 'rest': HTTP (experimental)
    authentication_keys : Optional[Tuple[PrivateKey, PublicKey]] (default: None)
        Tuple containing the elliptic curve private key and public key for
        authentication from the cryptography library.
        Source: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ec/
        Used to establish an authenticated connection with the server.
    max_retries: Optional[int] (default: None)
        The maximum number of times the client will try to connect to the
        server before giving up in case of a connection error. If set to None,
        there is no limit to the number of tries.
    max_wait_time: Optional[float] (default: None)
        The maximum duration before the client stops trying to
        connect to the server in case of connection error.
        If set to None, there is no limit to the total time.
    flwr_path: Optional[Path] (default: None)
        The fully resolved path containing installed Flower Apps.
    isolation : str (default: ISOLATION_MODE_SUBPROCESS)
        Isolation mode for `ClientApp`. Possible values are `subprocess` and
        `process`. If `subprocess`, the `ClientApp` runs in a subprocess started
        by the SueprNode and communicates using gRPC at the address
        `clientappio_api_address`. If `process`, the `ClientApp` runs in a separate
        isolated process and communicates using gRPC at the address
        `clientappio_api_address`.
    clientappio_api_address : str
        (default: `CLIENTAPPIO_API_DEFAULT_SERVER_ADDRESS`)
        The SuperNode gRPC server address.
    """
    if insecure is None:
        insecure = root_certificates is None

    # Initialize factories
    state_factory = NodeStateFactory()
    ffs_factory = FfsFactory(get_flwr_dir(flwr_path) / "supernode" / "ffs")  # type: ignore
    object_store_factory = ObjectStoreFactory()

    # Launch ClientAppIo API server
    clientappio_server = run_clientappio_api_grpc(
        address=clientappio_api_address,
        state_factory=state_factory,
        ffs_factory=ffs_factory,
        objectstore_factory=object_store_factory,
        certificates=None,
    )

    # Register handlers for graceful shutdown
    register_exit_handlers(
        event_type=EventType.RUN_SUPERNODE_LEAVE,
        exit_message="SuperNode terminated gracefully.",
        grpc_servers=[clientappio_server],
    )

    # Initialize NodeState, Ffs, and ObjectStore
    state = state_factory.state()
    ffs = ffs_factory.ffs()
    store = object_store_factory.store()

    with _init_connection(
        transport=transport,
        server_address=server_address,
        insecure=insecure,
        root_certificates=root_certificates,
        authentication_keys=authentication_keys,
        max_retries=max_retries,
        max_wait_time=max_wait_time,
    ) as conn:
        receive, send, create_node, _, get_run, get_fab = conn

        # Call create_node fn to register node
        # and store node_id in state
        if (node_id := create_node()) is None:
            raise ValueError("Failed to register SuperNode with the SuperLink")
        state.set_node_id(node_id)

        # pylint: disable=too-many-nested-blocks
        while True:
            # The signature of the function will change after
            # completing the transition to the `NodeState`-based SuperNode
            run_id = _pull_and_store_message(
                state=state,
                ffs=ffs,
                object_store=store,
                node_config=node_config,
                receive=receive,
                get_run=get_run,
                get_fab=get_fab,
            )

            # Two isolation modes:
            # 1. `subprocess`: SuperNode is starting the ClientApp
            #    process as a subprocess.
            # 2. `process`: ClientApp process gets started separately
            #    (via `flwr-clientapp`), for example, in a separate
            #    Docker container.

            # Mode 1: SuperNode starts ClientApp as subprocess
            start_subprocess = isolation == ISOLATION_MODE_SUBPROCESS

            if start_subprocess and run_id is not None:
                _octet, _colon, _port = clientappio_api_address.rpartition(":")
                io_address = (
                    f"{CLIENT_OCTET}:{_port}"
                    if _octet == SERVER_OCTET
                    else clientappio_api_address
                )
                # Start ClientApp subprocess
                command = [
                    "flwr-clientapp",
                    "--clientappio-api-address",
                    io_address,
                    "--parent-pid",
                    str(os.getpid()),
                    "--insecure",
                    "--run-once",
                ]
                subprocess.run(command, check=False)

            _push_messages(state=state, send=send)

            # Sleep for 3 seconds before the next iteration
            time.sleep(3)


def _pull_and_store_message(  # pylint: disable=too-many-positional-arguments
    state: NodeState,
    ffs: Ffs,
    object_store: ObjectStore,  # pylint: disable=unused-argument
    node_config: UserConfig,
    receive: Callable[[], Optional[Message]],
    get_run: Callable[[int], Run],
    get_fab: Callable[[str, int], Fab],
) -> Optional[int]:
    """Pull a message from the SuperLink and store it in the state.

    This function current returns None if no message is received,
    or run_id if a message is received and processed successfully.
    This behavior will change in the future to return None after
    completing transition to the `NodeState`-based SuperNode.
    """
    message = None
    try:
        # Pull message
        if (message := receive()) is None:
            return None

        # Log message reception
        log(INFO, "")
        if message.metadata.group_id:
            log(
                INFO,
                "[RUN %s, ROUND %s]",
                message.metadata.run_id,
                message.metadata.group_id,
            )
        else:
            log(INFO, "[RUN %s]", message.metadata.run_id)
        log(
            INFO,
            "Received: %s message %s",
            message.metadata.message_type,
            message.metadata.message_id,
        )

        # Ensure the run and FAB are available
        run_id = message.metadata.run_id

        # Check if the message is from an unknown run
        if (run_info := state.get_run(run_id)) is None:
            # Pull run info from SuperLink
            run_info = get_run(run_id)
            state.store_run(run_info)

            # Pull and store the FAB
            fab = get_fab(run_info.fab_hash, run_id)
            ffs.put(fab.content, {})

            # Initialize the context
            run_cfg = get_fused_config_from_fab(fab.content, run_info)
            run_ctx = Context(
                run_id=run_id,
                node_id=state.get_node_id(),
                node_config=node_config,
                state=RecordDict(),
                run_config=run_cfg,
            )
            state.store_context(run_ctx)

        # Store the message in the state
        # This shall be removed after the transition to ObjectStore
        state.store_message(message)

        # Store the message in ObjectStore
        # This is a temporary solution to store messages in ObjectStore
        with no_object_id_recompute():
            object_store.preregister(run_id, get_object_tree(message))
            for obj_id, obj in get_all_nested_objects(message).items():
                object_store.put(obj_id, obj.deflate())

    except RunNotRunningException:
        if message is None:
            log(
                INFO,
                "Run transitioned to a non-`RUNNING` status while receiving a message. "
                "Ignoring the message.",
            )
        else:
            log(
                INFO,
                "Run ID %s is not in `RUNNING` status. Ignoring message %s.",
                run_id,
                message.metadata.message_id,
            )
        return None

    return run_id


def _push_messages(
    state: NodeState,
    send: Callable[[Message], None],
) -> None:
    """Push reply messages to the SuperLink."""
    # Get messages to send
    reply_messages = state.get_messages(is_reply=True)

    for message in reply_messages:
        # Log message sending
        log(INFO, "")
        if message.metadata.group_id:
            log(
                INFO,
                "[RUN %s, ROUND %s]",
                message.metadata.run_id,
                message.metadata.group_id,
            )
        else:
            log(INFO, "[RUN %s]", message.metadata.run_id)
        log(
            INFO,
            "Sending: %s message",
            message.metadata.message_type,
        )

        # Send the message
        try:
            send(message)
            log(INFO, "Sent successfully")
        except RunNotRunningException:
            log(
                INFO,
                "Run ID %s is not in `RUNNING` status. Ignoring reply message %s.",
                message.metadata.run_id,
                message.metadata.message_id,
            )
        finally:
            # Delete the message from the state
            state.delete_messages(
                message_ids=[
                    message.metadata.message_id,
                    message.metadata.reply_to_message_id,
                ]
            )


@contextmanager
def _init_connection(  # pylint: disable=too-many-positional-arguments
    transport: str,
    server_address: str,
    insecure: bool,
    root_certificates: Optional[Union[bytes, str]] = None,
    authentication_keys: Optional[
        tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]
    ] = None,
    max_retries: Optional[int] = None,
    max_wait_time: Optional[float] = None,
) -> Iterator[
    tuple[
        Callable[[], Optional[Message]],
        Callable[[Message], None],
        Callable[[], Optional[int]],
        Callable[[], None],
        Callable[[int], Run],
        Callable[[str, int], Fab],
    ]
]:
    """Establish a connection to the Fleet API server at SuperLink."""
    # Parse IP address
    parsed_address = parse_address(server_address)
    if not parsed_address:
        flwr_exit(
            ExitCode.COMMON_ADDRESS_INVALID,
            f"SuperLink address ({server_address}) cannot be parsed.",
        )
    host, port, is_v6 = parsed_address
    address = f"[{host}]:{port}" if is_v6 else f"{host}:{port}"

    # Use either gRPC bidirectional streaming or REST request/response
    if transport == TRANSPORT_TYPE_REST:
        try:
            from requests.exceptions import ConnectionError as RequestsConnectionError

            from flwr.client.rest_client.connection import http_request_response
        except ModuleNotFoundError:
            flwr_exit(ExitCode.COMMON_MISSING_EXTRA_REST)
        if server_address[:4] != "http":
            flwr_exit(ExitCode.SUPERNODE_REST_ADDRESS_INVALID)
        connection, error_type = http_request_response, RequestsConnectionError
    elif transport == TRANSPORT_TYPE_GRPC_RERE:
        connection, error_type = grpc_request_response, RpcError
    elif transport == TRANSPORT_TYPE_GRPC_ADAPTER:
        connection, error_type = grpc_adapter, RpcError
    else:
        raise ValueError(
            f"Unknown transport type: {transport} (possible: {TRANSPORT_TYPES})"
        )

    # Create RetryInvoker
    retry_invoker = _make_fleet_connection_retry_invoker(
        max_retries=max_retries,
        max_wait_time=max_wait_time,
        connection_error_type=error_type,
    )

    # Establish connection
    with connection(
        address,
        insecure,
        retry_invoker,
        GRPC_MAX_MESSAGE_LENGTH,
        root_certificates,
        authentication_keys,
    ) as conn:
        yield conn


def _make_fleet_connection_retry_invoker(
    max_retries: Optional[int] = None,
    max_wait_time: Optional[float] = None,
    connection_error_type: type[Exception] = RpcError,
) -> RetryInvoker:
    """Create a retry invoker for fleet connection."""

    def _on_success(retry_state: RetryState) -> None:
        if retry_state.tries > 1:
            log(
                INFO,
                "Connection successful after %.2f seconds and %s tries.",
                retry_state.elapsed_time,
                retry_state.tries,
            )

    def _on_backoff(retry_state: RetryState) -> None:
        if retry_state.tries == 1:
            log(WARN, "Connection attempt failed, retrying...")
        else:
            log(
                WARN,
                "Connection attempt failed, retrying in %.2f seconds",
                retry_state.actual_wait,
            )

    return RetryInvoker(
        wait_gen_factory=lambda: exponential(max_delay=MAX_RETRY_DELAY),
        recoverable_exceptions=connection_error_type,
        max_tries=max_retries + 1 if max_retries is not None else None,
        max_time=max_wait_time,
        on_giveup=lambda retry_state: (
            log(
                WARN,
                "Giving up reconnection after %.2f seconds and %s tries.",
                retry_state.elapsed_time,
                retry_state.tries,
            )
            if retry_state.tries > 1
            else None
        ),
        on_success=_on_success,
        on_backoff=_on_backoff,
    )


def run_clientappio_api_grpc(
    address: str,
    state_factory: NodeStateFactory,
    ffs_factory: FfsFactory,
    objectstore_factory: ObjectStoreFactory,
    certificates: Optional[tuple[bytes, bytes, bytes]],
) -> grpc.Server:
    """Run ClientAppIo API gRPC server."""
    clientappio_servicer: grpc.Server = ClientAppIoServicer(
        state_factory=state_factory,
        ffs_factory=ffs_factory,
        objectstore_factory=objectstore_factory,
    )
    clientappio_add_servicer_to_server_fn = add_ClientAppIoServicer_to_server
    clientappio_grpc_server = generic_create_grpc_server(
        servicer_and_add_fn=(
            clientappio_servicer,
            clientappio_add_servicer_to_server_fn,
        ),
        server_address=address,
        max_message_length=GRPC_MAX_MESSAGE_LENGTH,
        certificates=certificates,
    )
    log(INFO, "Starting Flower ClientAppIo gRPC server on %s", address)
    clientappio_grpc_server.start()
    return clientappio_grpc_server
