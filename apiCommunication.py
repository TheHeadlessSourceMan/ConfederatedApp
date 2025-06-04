import typing
import time
import asyncio
import threading
import uuid
import queue
import traceback
from concurrent.futures import ProcessPoolExecutor
import ssl
import websocket as ws
import websockets.server
import websockets
from jsonHelper import JsonCompatible,JsonLike,asJson,asJsonStr
from machineIdentity import NetworkLocation


EndpointCallable=typing.Callable[...,JsonCompatible]


class ApiHandler:
    """
    A handler that can manage and execute api endpoints.

    This supports asynchronous calling with full
    multithreading, multiprocessing, and asyncio

    TODO: this needs to go away in favor of a FunctionCallManager
    """
    def __init__(self):
        self._localEndpoints:typing.Dict[str,
            typing.Tuple[EndpointCallable,bool]]={}
        self._keepGoing=True
        self._toBeProcessed=queue.Queue()
        self._processPoolExecutor:typing.Optional[ProcessPoolExecutor]=None
        self._processThread:typing.Optional[threading.Thread]=None

    def start(self,restart:bool=False)->None:
        """
        Start the messaging system.
        (Will automatically start.  No need to call this manually.)
        """
        if restart and self._processThread:
            self.stop()
        if self._processThread is not None:
            self._processPoolExecutor=ProcessPoolExecutor()
            self._keepGoing=True
            self._processThread=threading.Thread(
                target=self._processDataLoop,daemon=True)
            self._processThread.start()

    def __del__(self):
        self.stop()

    def stop(self):
        """
        Stop the message processing thread
        """
        while self._processThread is not None:
            self._keepGoing=False
            time.sleep(0.1)
        if self._processPoolExecutor is not None:
            self._processPoolExecutor.shutdown()
            self._processPoolExecutor=None

    def _processDataLoop(self):
        """
        Pulls requests out of the queue and processes them
        """
        while self._keepGoing:
            try:
                request=self._toBeProcessed.get(timeout=0.01)
                endpoint=self._localEndpoints.get(
                    request.get('endpoint',''))
                if endpoint is None:
                    if 'requestId' in request:
                        endpoint.send({
                            'responseId':request['requestId'],
                            'status':404})
                    continue
                if endpoint[1]:
                    # call callLocalEndpoint() as separate process
                    def callback(future):
                        response=future.result()
                        asyncio.run_coroutine_threadsafe(
                            self.socket.send(response),self.loop)
                    future=self._processPoolExecutor.submit(
                        self.callLocalEndpoint,endpoint[0],request)
                    future.add_done_callback(callback)
                    continue
                # call callLocalEndpoint() as a separate thread
                asyncio.run_coroutine_threadsafe(
                    self.socket.send(
                        self.callLocalEndpoint(endpoint[0],request)),
                    self.loop)
            except queue.Empty:
                time.sleep(1.0)
                continue
            except Exception as e:
                print("Processing error:",e)
        self._processThread=None

    def callLocalEndpoint(self,
        endpointFn:EndpointCallable,
        request:JsonLike
        )->JsonLike:
        """
        This code will either be called in a separate thread
        or a separate cpu process, depending on how the Endpoint
        was registered.
        """
        try:
            response=asJson(
                endpointFn(
                    *request.get('args',[]),
                    **request.get('kwargs',{})))
        except Exception as e:
            response={
                'status':500,
                'exception':traceback.format_exception(e)}
        if 'status' not in response:
            response['status']=200
        if 'responseId' not in response:
            response['responseId']=request['requestId']
        return response

    def addLocalEndpoint(self,
        endpoint:EndpointCallable,
        name:typing.Optional[str]=None,
        asProcess:bool=False)->None:
        """
        Add a new endpoint to the list.

        :endpoint: the endpoint functionto call with requests
        :name: if no name is specified, use the function name of the endpoint
        :asProcess: this can be run as a separate process (as opposed to a
            separate thread under the GIL lock)
        """
        if name is None:
            name=endpoint.__name__
        self._localEndpoints[name]=(endpoint,asProcess)

    def removeLocalEndpoint(self,
        endpoint:typing.Union[str,EndpointCallable]
        )->None:
        """
        Remove an endpoint from the list
        """
        if isinstance(endpoint,str):
            del self._localEndpoints[endpoint]
            return
        names=[]
        if not isinstance(endpoint,str):
            for name,bfn in self._localEndpoints:
                if bfn[0]==endpoint:
                    names.append(name)
        for endpoint in names:
            del self._localEndpoints[endpoint]


class ApiCommunication:
    """
    Bidirectional api connection to a remote device

    This supports asynchronous communication with full
    multithreading, multiprocessing, and asyncio

    TODO: need this to work as a bidirectional peer
    (that is, client or server).
    TODO: attach to a single common ApiHandler, or better
    yet, FunctionCallManager, to handle all execution
    """
    def __init__(self,
        networkAddress:NetworkLocation,
        apiHandler:ApiHandler,
        useSecureConnection:bool=True):
        """ """
        self.apiHandler=apiHandler
        self._useSecureConnection=useSecureConnection
        self._sslContext:typing.Optional[ssl.SSLContext]=None
        if self._useSecureConnection:
            self._sslContext=ssl.create_default_context(
                ssl.Purpose.SERVER_AUTH)
            self._sslContext.load_cert_chain(
                certfile="certs/client.crt",
                keyfile="certs/client.key")
            self._sslContext.load_verify_locations("certs/ca.crt") # Trust CA that signed server
            self._sslContext.check_hostname=True
            self._sslContext.verify_mode=ssl.CERT_REQUIRED
        self._networkAddress=networkAddress
        self._socket:typing.Optional[ws.WebSocket]=None
        self._awaitingResponse={}
        self._keepGoing=True
        self.start()

    def start(self):
        """
        Start the messaging system.
        (Will automatically start.  No need to call this manually.)
        """
        self.loop=asyncio.new_event_loop()
        self._processPoolExecutor=ProcessPoolExecutor()
        self.thread=threading.Thread(
            target=self._startLoop,daemon=True)
        self.thread.start()
        # Thread to receive and queue incoming messages
        self.recv_thread=threading.Thread(
            target=self._startRecieveloop,daemon=True)
        self.recv_thread.start()
        self.apiHandler.start()

    def stop(self):
        """
        Stop all communication and close the socket
        """
        self._keepGoing=False
        socket=self._socket
        if socket:
            self._socket=None
            asyncio.run_coroutine_threadsafe(socket.close(),self.loop)
    close=stop
    disconnect=stop
    def __del__(self):
        self.stop()

    def _startLoop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.socket)

    async def _socketReceiveLoop(self):
        """
        Queue up all incoming requests
        and notify original callers of all incoming responses.
        """
        while self._keepGoing:
            message=await self.socket.recv()
            data=asJson(message)
            if 'responseId' in data:
                # This is a response to a previous request
                future=self._awaitingResponse.pop(data['responseId'],None)
                if future:
                    future.set_result(data['payload'])
            else:
                # This is a new incoming request
                self._toBeProcessed.put(data)

    def _startRecieveloop(self):
        """
        Start the asyncio loop that receives messages
        """
        asyncio.run(self._socketReceiveLoop())

    async def sendJsonMessage(self,message:JsonCompatible)->JsonLike:
        """
        Ask a Json question, get a Json answer.
        """
        message=asJson(message)
        if 'requestId' not in message:
            message['requestId']=str(uuid.uuid4())
        future=self.loop.create_future()
        self._awaitingResponse[message['requestId']]=future
        await self.socket.send(asJsonStr(message))
        return await future

    def callRemoteEndpoint(self,commandName:str,*args,**kwargs)->JsonLike:
        """
        Calls a remote endpoint of the form:
        {
            'endpoint':'',
            'args':[],
            'kwargs':{}
        }
        Return a json response.
        """
        msg={
            'endpoint':commandName,
            'args':asJson(args),
            'kwargs':asJson(kwargs)
        }
        self.socket.send(msg)
        jsonStr=self.socket.recv()
        return asJson(jsonStr)
    __call__=callRemoteEndpoint

    @property
    def url(self)->str:
        """
        Get the websocket url
        """
        protocol='ws'
        if self._useSecureConnection:
            protocol='wss'
        return f'{protocol}://{self.networkAddress}'

    @property
    def networkAddress(self)->str:
        """
        Get the websocket address
        """
        return self._networkAddress

    @property
    def socket(self)->ws.WebSocket:
        """
        Get a websocket instance.

        (Connect if necessary)
        """
        if self._socket is None:
            self.connect()
        return self._socket

    def connect(self,reconnect:bool=False)->None:
        """
        Connect the socket.

        (Will be called automatically as needed)
        """
        if reconnect or self._socket is None:
            if self._useSecureConnection:
                self._socket=ws.create_connection(self.url,1)
            else:
                self._socket=ws.create_connection(
                    self.url,1,ssl=self._sslContext)
            asyncio.ensure_future(self._socketReceiveLoop())


class ApiServer:
    """
    Set up a server to listen for connections

    TODO: somehow need to spawn an ApiCommunication object
    for every authenticated client that connects.
    """
    def __init__(self):
        self._server:typing.Optional[websockets.server.ServerConnection]=None
        self._sslContext:typing.Optional[ssl.SSLContext]=None
        self._sslContext=ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self._sslContext.load_cert_chain(
            certfile="certs/server.crt",
            keyfile="certs/server.key")
        self._sslContext.load_verify_locations("certs/ca.crt")
        # Require client certificate
        self._sslContext.verify_mode=ssl.CERT_REQUIRED

    def start(self):
        """
        Start the server
        """
        async def handler(websocket,path):
            # You can inspect the client's certificate here
            peer_cert=websocket.transport.get_extra_info('peercert')
            print(path,"Client cert:",peer_cert)
        self._server=websockets.server.serve(
            handler,"localhost",18765,ssl=self._sslContext)
        asyncio.get_event_loop().run_until_complete(self._server)
        asyncio.get_event_loop().run_forever()

s=ApiServer()
s.start()